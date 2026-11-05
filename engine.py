"""Rule engine for invented-domain policies.

A policy is an ordered list of rules over typed facts with small finite domains (ints bucketed to at
most 8 values, enums, bools). Derived facts (a date gap, a sum) are named expressions over source facts:
rules may use them, the engine recomputes them from their sources and they are never edited directly.
Require rules hold a condition and an optional "unless" exception that waives them. Default rules fill
a missing fact before evaluation. Validity conditions (end date after start date) define which complete
assignments are admissible.

Conditions are Python expressions restricted to comparisons, and/or/not, membership, + - * //, fact
names and constants, compiled once into lambdas over a fact dict.

The decision over a partial record (after defaults) is approve if every admissible completion
approves, deny if every one denies, "cannot determine" if both occur, and an InvalidRecord error if
there is no admissible completion. A set S of known facts is sufficient when every admissible
completion z with z_S = x_S gets the same decision as x. Checks are exact: a backtracking search over
the omitted facts' domains, split into independent components and cached. Searches run under a
per-case time budget and report "uncertified" with a reason instead of truncating silently.

Edits come in three kinds: replace (observed value -> another value, used by min_flip and
invariant_edit), remove (observation deleted, defaults may fire) and add (a missing fact revealed,
used by min_reveal). On top of decide() sit cd_witnesses(), sufficient_sets(), necessary_facts(),
single_condition(), min_flip(), min_reveal(), invariant_edit() and is_valid_justification(), all
deterministic.
"""
import ast
import functools
import itertools
import time

MAX_DOM, MAX_FACTS, MAX_RADIUS, BUDGET = 8, 12, 4, 2.0


class InvalidRecord(ValueError):
    """
    Signals a record (or partial record) with no admissible completion.
    """


class Timeout(RuntimeError):
    """
    Signals that a search ran past its per-case budget; callers report the result as uncertified.
    """
OPS = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not, ast.USub, ast.BinOp, ast.Add,
       ast.Sub, ast.Mult, ast.FloorDiv, ast.Compare, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.NotEq,
       ast.In, ast.NotIn, ast.Name, ast.Constant, ast.Tuple, ast.List, ast.Load)


def compile_cond(src, names, derived=None):
    """
    Returns (fn, refs) for a condition string: fn maps a fact dict to bool, refs lists the source facts
    it reads in first-use order. Derived fact names are expanded into their expressions first.
    Raises ValueError on syntax outside the condition language or unknown names.
    """
    derived = derived or {}
    tree = ast.parse(src, mode="eval")
    for nd in ast.walk(tree):
        if not isinstance(nd, OPS):
            raise ValueError(f"unsupported syntax {type(nd).__name__} in {src!r}")

    class Sub(ast.NodeTransformer):
        """
        Expands derived names and rewrites each source fact name into a lookup f["name"].
        """

        def visit_Name(self, nd):
            """
            Returns the expanded expression for a derived name or the subscript for a source fact.
            """
            if nd.id in derived:
                return self.visit(ast.parse(derived[nd.id], mode="eval").body)
            if nd.id not in names:
                raise ValueError(f"unknown fact {nd.id!r} in {src!r}")
            if nd.id not in refs:
                refs.append(nd.id)
            return ast.copy_location(ast.Subscript(value=ast.Name("f", ast.Load()), slice=ast.Constant(nd.id),
                                                   ctx=ast.Load()), nd)

    refs = []
    body = Sub().visit(tree).body
    lam = ast.Expression(ast.Lambda(ast.arguments(posonlyargs=[], args=[ast.arg("f")], kwonlyargs=[],
                                                  kw_defaults=[], defaults=[]), body))
    ast.fix_missing_locations(lam)
    return eval(compile(lam, "<cond>", "eval"), {"__builtins__": {}}), refs


class Rule:
    """
    Holds one require rule: id, condition, optional exception and compiled lambdas.
    """

    def __init__(self, d, names, derived):
        """
        Builds the rule from a spec dict with keys id, cond and unless (optional).
        """
        self.id, self.cond, self.unless = d["id"], d["cond"], d.get("unless")
        self.fc, self.refs = compile_cond(self.cond, names, derived)
        self.fu, self.urefs = (None, []) if not self.unless else compile_cond(self.unless, names, derived)
        self.all_refs = self.refs + [n for n in self.urefs if n not in self.refs]

    def holds(self, f):
        """
        Returns True when the rule is satisfied or waived on a complete assignment f.
        """
        return bool(self.fc(f)) or (self.fu is not None and bool(self.fu(f)))


class Policy:
    """
    Holds a policy: fact schema, derived facts, require rules, defaults, validity conditions and caches.
    """

    def __init__(self, pid, facts, rules, valid=(), derived=None):
        """
        Builds a policy. facts: {name: spec} with spec {"type": "int", "values": [...]} (or lo/hi/step),
        {"type": "enum", "values": [...]} or {"type": "bool"}. derived: {name: expression over facts}.
        rules: ordered spec dicts, {"id", "kind": "require", "cond", "unless"?} or
        {"id", "kind": "default", "fact", "value"}. valid: conditions every admissible assignment meets.
        """
        self.id, self.facts, self.order, self.derived = pid, facts, list(facts), dict(derived or {})
        self.dom = {}
        for n, s in facts.items():
            if s["type"] == "bool":
                self.dom[n] = [False, True]
            elif "values" in s:
                self.dom[n] = list(s["values"])
            else:
                self.dom[n] = list(range(s["lo"], s["hi"] + 1, s.get("step", 1)))
            if len(self.dom[n]) > MAX_DOM:
                raise ValueError(f"{n} has {len(self.dom[n])} values, max {MAX_DOM}")
        names = set(facts)
        self.dfn = {n: compile_cond(e, names, self.derived) for n, e in self.derived.items()}
        self.requires, self.defaults = [], {}
        for d in rules:
            if d["kind"] == "default":
                if d["value"] not in self.dom[d["fact"]]:
                    raise ValueError(f"default {d['value']!r} outside domain of {d['fact']}")
                self.defaults[d["fact"]] = (d["id"], d["value"])
            else:
                self.requires.append(Rule(d, names, self.derived))
        self.valid = [compile_cond(v, names, self.derived) for v in valid]
        self.cons = {}
        for i, (fn, refs) in enumerate(self.valid):
            self.cons[f"v{i}"] = (fn, refs)
        for r in self.requires:
            self.cons["+" + r.id] = (r.holds, r.all_refs)
            self.cons["-" + r.id] = (lambda f, r=r: not r.holds(f), r.all_refs)
            self.cons["c" + r.id] = (r.fc, r.refs)
        self.cache, self.deadline = {}, None
        if len(self.referenced()) > MAX_FACTS:
            raise ValueError(f"policy reads {len(self.referenced())} facts, max {MAX_FACTS}")

    def ok(self, f):
        """
        Returns True when f meets every validity condition whose facts it states.
        """
        return all(fn(f) for fn, refs in self.valid if all(n in f for n in refs))

    def referenced(self):
        """
        Returns the source facts read by any require rule or validity condition, in schema order.
        """
        used = set()
        for r in self.requires:
            used.update(r.all_refs)
        for _, refs in self.valid:
            used.update(refs)
        return [n for n in self.order if n in used]

    def derived_values(self, f):
        """
        Returns {derived name: value} for every derived fact whose sources f states.
        """
        out = {}
        for n, (fn, refs) in self.dfn.items():
            if all(x in f for x in refs):
                out[n] = fn(f)
        return out


def known_facts(pol, facts):
    """
    Returns (known, defaults_applied): stated source facts plus defaults for missing facts that have one.
    """
    known = {n: v for n, v in facts.items() if n in pol.facts and v is not None}
    applied = {}
    for n, (_, v) in pol.defaults.items():
        if n not in known:
            known[n], applied[n] = v, v
    return known, applied


def fact_states(pol, facts):
    """
    Returns {name: state} for every source and derived fact: observed {value}, missing, default
    {value, rule} or derived {value, sources} (derived value None when a source is missing).
    """
    known, applied = known_facts(pol, facts)
    out = {}
    for n in pol.order:
        if n in applied:
            out[n] = {"state": "default", "value": applied[n], "rule": pol.defaults[n][0]}
        elif n in known:
            out[n] = {"state": "observed", "value": known[n]}
        else:
            out[n] = {"state": "missing"}
    dv = pol.derived_values(known)
    for n, (_, refs) in pol.dfn.items():
        out[n] = {"state": "derived", "value": dv.get(n), "sources": refs}
    return out


def budgeted(fn):
    """
    Returns fn wrapped so that its outermost call sets pol.deadline to now + budget seconds (keyword
    budget, default BUDGET) and clears it on exit. Searches raise Timeout once the deadline passes.
    """

    @functools.wraps(fn)
    def run(pol, *a, budget=BUDGET, **kw):
        """
        Runs fn under the policy deadline, setting the deadline only on the outermost budgeted call.
        """
        outer = pol.deadline is None
        if outer:
            pol.deadline = time.monotonic() + budget
        try:
            return fn(pol, *a, **kw)
        finally:
            if outer:
                pol.deadline = None

    return run


def tick(pol):
    """
    Raises Timeout when the policy's current search deadline has passed.
    """
    if pol.deadline is not None and time.monotonic() > pol.deadline:
        raise Timeout(f"search budget exceeded for {pol.id}")


def solve(pol, keys, known):
    """
    Returns values for omitted facts that, with `known`, satisfy every constraint in `keys` (ids into
    pol.cons) plus all validity conditions, or None when no admissible completion does. Splits the
    constraints into independent components and backtracks, checking each constraint once its facts
    are set. Facts outside every constraint are left out of the returned dict.
    """
    keys = list(keys) + [k for k in pol.cons if k[0] == "v"]
    key = ("s", tuple(sorted(keys)), tuple(sorted((n, repr(v)) for n, v in known.items())))
    if key in pol.cache:
        return pol.cache[key]
    comps, res = [], {}
    for k in keys:
        fn, refs = pol.cons[k]
        fr = {n for n in refs if n not in known}
        if not fr:
            if not fn(known):
                res = None
            continue
        hit = [c for c in comps if c[0] & fr]
        for c in hit:
            comps.remove(c)
            fr |= c[0]
        comps.append((fr, [x for c in hit for x in c[1]] + [k]))
    for fr, ks in comps if res is not None else []:
        free = sorted(fr, key=lambda n: (-sum(n in pol.cons[k][1] for k in ks), pol.order.index(n)))
        ready = []
        for i in range(len(free)):
            done = set(free[:i + 1])
            ready.append([pol.cons[k][0] for k in ks if free[i] in pol.cons[k][1] and
                          all(n in known or n in done for n in pol.cons[k][1])])
        f = dict(known)

        def dfs(i):
            """
            Returns True when omitted facts i.. admit values meeting every constraint checked at their depth.
            """
            tick(pol)
            if i == len(free):
                return True
            for v in pol.dom[free[i]]:
                f[free[i]] = v
                if all(fn(f) for fn in ready[i]) and dfs(i + 1):
                    return True
            return False

        if not dfs(0):
            res = None
            break
        res.update({n: f[n] for n in free})
    pol.cache[key] = res
    return res


def sat(pol, keys, known):
    """
    Returns True when some admissible completion of `known` satisfies the constraints in `keys`.
    """
    return solve(pol, keys, known) is not None


def possible(pol, known):
    """
    Returns the set of decisions ("approve", "deny") reached by admissible completions of `known`.
    Raises InvalidRecord when no admissible completion exists.
    """
    key = ("p", tuple(sorted((n, repr(v)) for n, v in known.items())))
    if key not in pol.cache:
        out = set()
        if sat(pol, ["+" + r.id for r in pol.requires], known):
            out.add("approve")
        if any(sat(pol, ["-" + r.id], known) for r in pol.requires):
            out.add("deny")
        if not out:
            raise InvalidRecord(f"no admissible completion of {sorted(known)} under {pol.id}")
        pol.cache[key] = out
    return pol.cache[key]


def decide(pol, facts, rid=None):
    """
    Returns {"decision", "rule_trace", "defaults_applied", "needs_fact_for"} for a fact dict that may
    omit facts. Approve if every admissible completion approves, deny if every one denies, else
    "cannot determine". rule_trace maps each require rule id to pass, fail, waived or unknown;
    needs_fact_for lists the unknown rules when the decision is "cannot determine". Raises
    InvalidRecord naming record `rid` when the record has no admissible completion.
    """
    known, applied = known_facts(pol, facts)
    try:
        poss = possible(pol, known)
    except InvalidRecord as e:
        raise InvalidRecord(f"record {rid}: {e}") from None
    dec = "cannot determine" if len(poss) == 2 else next(iter(poss))
    trace = {}
    for r in pol.requires:
        if not sat(pol, ["-" + r.id], known):
            trace[r.id] = "waived" if not sat(pol, ["c" + r.id], known) else "pass"
        else:
            trace[r.id] = "fail" if not sat(pol, ["+" + r.id], known) else "unknown"
    needs = [rid for rid, s in trace.items() if s == "unknown"] if dec == "cannot determine" else []
    return {"decision": dec, "rule_trace": trace, "defaults_applied": applied, "needs_fact_for": needs}


def cd_witnesses(pol, facts):
    """
    Returns {"approve": {...}, "deny": {...}}: values for every omitted fact that complete the record
    admissibly with that decision (both exist exactly when the decision is "cannot determine"), with
    None for a side that has no completion.
    """
    known, _ = known_facts(pol, facts)
    omitted = [n for n in pol.order if n not in known]
    sols = {"approve": solve(pol, ["+" + r.id for r in pol.requires], known), "deny": None}
    for r in pol.requires:
        sols["deny"] = solve(pol, ["-" + r.id], known)
        if sols["deny"] is not None:
            break
    out = {}
    for d, s in sols.items():
        out[d] = None if s is None else {n: s.get(n, pol.dom[n][0]) for n in omitted}
    return out


@budgeted
def sufficient_sets(pol, facts):
    """
    Returns every subset-minimal set of known source facts (stated plus defaulted) that alone forces the
    decision, as lists in schema order, smallest first. Returns [] for "cannot determine". Raises
    Timeout when the budget runs out (callers record the item as uncertified).
    """
    known, _ = known_facts(pol, facts)
    dec = decide(pol, facts)["decision"]
    if dec == "cannot determine":
        return []
    cand = [n for n in pol.referenced() if n in known]
    found = []
    for k in range(len(cand) + 1):
        for sub in itertools.combinations(cand, k):
            s = set(sub)
            if any(f <= s for f in found):
                continue
            if possible(pol, {n: known[n] for n in sub}) == {dec}:
                found.append(s)
    return [[n for n in pol.order if n in s] for s in found]


def necessary_facts(pol, facts, sets=None):
    """
    Returns the facts that appear in every minimal sufficient set, in schema order.
    """
    sets = sufficient_sets(pol, facts) if sets is None else sets
    if not sets:
        return []
    common = set(sets[0])
    for s in sets[1:]:
        common &= set(s)
    return [n for n in pol.order if n in common]


def single_condition(pol, facts, sets=None):
    """
    Returns True when one rule decides the case: exactly one failed rule for deny, exactly one
    unknown rule for "cannot determine", and a unique minimal sufficient set for approve.
    """
    d = decide(pol, facts)
    if d["decision"] == "deny":
        return sum(s == "fail" for s in d["rule_trace"].values()) == 1
    if d["decision"] == "cannot determine":
        return len(d["needs_fact_for"]) == 1
    return len(sufficient_sets(pol, facts) if sets is None else sets) == 1


def flip_target(decision):
    """
    Returns the fixed own-boundary target label for a decision: approve <-> deny, None for "cannot determine".
    """
    return {"approve": "deny", "deny": "approve"}.get(decision)


@budgeted
def min_flip(pol, facts, target=None, radius=MAX_RADIUS):
    """
    Returns the smallest "replace" edit of stated source facts that makes the decision `target`
    (default flip_target of the current decision), searching by increasing number of edited facts up to
    `radius` and preferring the smallest total move in bucket steps, then schema order. Edits must stay
    admissible; for deny, the edited facts must touch every failed rule. Found: {"kind": "replace",
    "edits", "radius", "certified_minimum": True, "target"}. Certified absence within the radius:
    {"kind", "edits": None, "exhausted_radius", "target"}. Over budget: {"kind", "edits": None,
    "searched_radius", "uncertified": True, "reason", "target"}. "cannot determine": edits and target None.
    """
    d = decide(pol, facts)
    tgt = target or flip_target(d["decision"])
    if d["decision"] == "cannot determine":
        return {"kind": "replace", "edits": None, "target": None}
    if tgt == d["decision"] or tgt not in ("approve", "deny"):
        raise ValueError(f"target {tgt!r} is not a flip from {d['decision']!r}")
    known, _ = known_facts(pol, facts)
    want = tgt == "approve"
    cand = [n for n in pol.referenced() if n in facts and facts[n] is not None]
    full = all(n in known for n in pol.referenced())
    failed = [r for r in pol.requires if d["rule_trace"][r.id] == "fail"] if want else []
    k = 0
    try:
        for k in range(1, radius + 1):
            best = None
            for combo in itertools.combinations(cand, k):
                tick(pol)
                if any(not set(combo) & set(r.all_refs) for r in failed):
                    continue
                alts = [[v for v in pol.dom[n] if v != known[n]] for n in combo]
                for vals in itertools.product(*alts):
                    f = {**known, **dict(zip(combo, vals))}
                    if not pol.ok(f):
                        continue
                    hit = all(r.holds(f) for r in pol.requires) == want if full else possible(pol, f) == {tgt}
                    if hit:
                        c = (sum(abs(pol.dom[n].index(v) - pol.dom[n].index(known[n])) for n, v in zip(combo, vals)),
                             [pol.order.index(n) for n in combo])
                        if best is None or c < best[0]:
                            best = (c, dict(zip(combo, vals)))
            if best:
                return {"kind": "replace", "edits": best[1], "radius": k, "certified_minimum": True, "target": tgt}
    except Timeout as e:
        return {"kind": "replace", "edits": None, "searched_radius": k - 1, "uncertified": True,
                "reason": f"{e} at radius {k}", "target": tgt}
    return {"kind": "replace", "edits": None, "exhausted_radius": radius, "target": tgt}


@budgeted
def min_reveal(pol, facts, radius=2):
    """
    Returns the smallest "add" edit for a "cannot determine" record: unstated facts with values whose
    revelation decides the case, by increasing number of facts up to `radius` (smallest bucket indices,
    then schema order). Found: {"kind": "add", "adds", "radius", "certified_minimum": True, "decision"}.
    Certified absence within the radius: {"kind", "adds": None, "exhausted_radius"}. Over budget:
    {"kind", "adds": None, "searched_radius", "uncertified": True, "reason"}. Decided records get
    {"kind": "add", "adds": None}.
    """
    if decide(pol, facts)["decision"] != "cannot determine":
        return {"kind": "add", "adds": None}
    known, _ = known_facts(pol, facts)
    cand = [n for n in pol.referenced() if facts.get(n) is None]
    k = 0
    try:
        for k in range(1, radius + 1):
            best = None
            for combo in itertools.combinations(cand, k):
                tick(pol)
                for vals in itertools.product(*(pol.dom[n] for n in combo)):
                    try:
                        poss = possible(pol, {**known, **dict(zip(combo, vals))})
                    except InvalidRecord:
                        continue
                    c = (sum(pol.dom[n].index(v) for n, v in zip(combo, vals)), [pol.order.index(n) for n in combo])
                    if len(poss) == 1 and (best is None or c < best[0]):
                        best = (c, dict(zip(combo, vals)), next(iter(poss)))
            if best:
                return {"kind": "add", "adds": best[1], "radius": k, "certified_minimum": True, "decision": best[2]}
    except Timeout as e:
        return {"kind": "add", "adds": None, "searched_radius": k - 1, "uncertified": True,
                "reason": f"{e} at radius {k}"}
    return {"kind": "add", "adds": None, "exhausted_radius": radius}


def invariant_edit(pol, facts, rng, sets=None):
    """
    Returns an admissible "replace" edit {fact: value} to one stated fact outside every minimal
    sufficient set that keeps the decision, or None. Prefers facts some rule reads, so the edit looks relevant.
    """
    dec = decide(pol, facts)["decision"]
    if dec == "cannot determine":
        return None
    sets = sufficient_sets(pol, facts) if sets is None else sets
    used = set()
    for s in sets:
        used.update(s)
    live = set(pol.referenced())
    cand = [n for n in pol.order if n in facts and facts[n] is not None and n not in used]
    cand.sort(key=lambda n: (n not in live, rng.random()))
    for n in cand:
        vals = [v for v in pol.dom[n] if v != facts[n]]
        rng.shuffle(vals)
        for v in vals:
            g = {**facts, n: v}
            if pol.ok(known_facts(pol, g)[0]) and decide(pol, g)["decision"] == dec:
                return {n: v}
    return None


def coerce(pol, n, v):
    """
    Returns v converted to the type of fact n (ints, bools and enums from strings), or v unchanged.
    """
    s = pol.facts.get(n)
    if s is None or not isinstance(v, str):
        return v
    t = v.strip().strip("'\"").lower()
    if s["type"] == "bool":
        return t in ("true", "yes", "1")
    if s["type"] == "int":
        try:
            return int(t.replace(",", "").replace("$", ""))
        except ValueError:
            return v
    for x in pol.dom[n]:
        if str(x).lower() == t:
            return x
    return v


@budgeted
def is_valid_justification(pol, facts, cited_facts, cited_rules, assumptions):
    """
    Returns {"valid", "sufficient", "minimal", "could_decide", "covers_needed", "wrong_rules",
    "wrong_assumptions", "missing_defaults", "wrong_values"} for a model's account.
    cited_facts {name: value} may name derived facts, which canonicalize to their source facts in every
    view. cited_rules is a flat list of rule ids (or {fact: rule id or [ids]}); each require rule must
    read a cited fact or assumption, and each default rule must belong to a stated assumption.
    assumptions {name: value or [value, rule id]}: each must name a fact that is missing with a default
    applied, with the default's value (and rule), else it is a wrong assumption and the account invalid.
    Decided records: sufficient when the cited source facts plus correct assumptions force the decision,
    minimal when no cited fact can be dropped (assumptions never count against minimality).
    "cannot determine": the cited missing facts must cover a set whose revelation could decide the case
    (could_decide, also "sufficient"); covers_needed says whether they include every missing fact behind
    needs_fact_for; minimal is None. wrong_rules also flags, for deny, rules that did not fail.
    missing_defaults: applied defaults not stated as assumptions that are necessary, that the cited facts
    need, or (for "cannot determine") that an undecided rule reads. Over budget: valid False,
    "uncertified": True, reason "uncertified".
    """
    try:
        known, applied = known_facts(pol, facts)
        d = decide(pol, facts)
        cd = d["decision"] == "cannot determine"
        dv = pol.derived_values(known)
        S, M, wrong_vals, assumed, wrong_asm = set(), set(), [], set(), []
        for n, v in cited_facts.items():
            if n in pol.dfn and n in dv:
                if coerce(pol, n, v) != dv[n] and str(v).strip() != str(dv[n]):
                    wrong_vals.append(n)
                S.update(pol.dfn[n][1])
            elif n in pol.dfn:
                S.update(x for x in pol.dfn[n][1] if x in known)
                M.update(x for x in pol.dfn[n][1] if x not in known)
            elif n in known:
                S.add(n)
                if coerce(pol, n, v) != known[n]:
                    wrong_vals.append(n)
            elif n in pol.facts:
                M.add(n)
            else:
                wrong_vals.append(n)
        if M and not cd:
            wrong_vals.extend(sorted(M))
        for n, v in assumptions.items():
            val, arid = (v[0], v[1]) if isinstance(v, (list, tuple)) and len(v) == 2 else (v, None)
            if n in applied and coerce(pol, n, val) == applied[n] and arid in (None, pol.defaults[n][0]):
                assumed.add(n)
            else:
                wrong_asm.append(n)
        rmap = {r.id: r for r in pol.requires}
        dfact = {rid: n for n, (rid, _) in pol.defaults.items()}
        pairs = list(cited_rules.items()) if isinstance(cited_rules, dict) else [(None, x) for x in cited_rules]
        wrong = []
        for n, rids in pairs:
            for rid in [rids] if isinstance(rids, str) else rids:
                r = rmap.get(rid)
                reads = (set(pol.dfn[n][1]) if n in pol.dfn else {n}) if n is not None else S | M | assumed
                if r is None:
                    bad = rid not in dfact or dfact[rid] not in assumed
                else:
                    bad = not set(r.all_refs) & reads or (d["decision"] == "deny" and d["rule_trace"][rid] != "fail")
                if bad and rid not in wrong:
                    wrong.append(rid)

        def forces(sub):
            """
            Returns True when the known values of `sub` alone force the engine decision.
            """
            return possible(pol, {n: known[n] for n in sub if n in known}) == {d["decision"]}

        could = covers = None
        if cd:
            needed = {n for r in pol.requires if r.id in d["needs_fact_for"] for n in r.all_refs if n not in known}
            ms = sorted(M, key=pol.order.index)
            could = False
            for vals in itertools.product(*(pol.dom[n] for n in ms)) if ms else []:
                try:
                    could = len(possible(pol, {**known, **dict(zip(ms, vals))})) == 1
                except InvalidRecord:
                    continue
                if could:
                    break
            covers = needed <= M
            readers = {n for r in pol.requires if r.id in d["needs_fact_for"] for n in r.all_refs}
            missing = [n for n in applied if n not in assumed and n in readers]
            suff, mini = could, None
        else:
            nec = set(necessary_facts(pol, facts))
            missing = [n for n in applied if n not in assumed and (n in nec or not forces(S | assumed) and
                                                                   forces(S | assumed | {n}))]
            suff, base = forces(S | assumed), set() if forces(S) else assumed
            mini = suff and all(not forces((S - {n}) | base) for n in S)
        valid = bool(suff and (mini or cd) and not wrong and not wrong_asm and not missing and not wrong_vals)
        return {"valid": valid, "sufficient": suff, "minimal": mini, "could_decide": could, "covers_needed": covers,
                "wrong_rules": wrong, "wrong_assumptions": wrong_asm, "missing_defaults": missing,
                "wrong_values": wrong_vals}
    except Timeout as e:
        return {"valid": False, "uncertified": True, "reason": "uncertified", "detail": str(e)}
