import copy

initialFile = open('initial.txt')

def parse(st):
    current = ""
    parsed = []
    i = 0
    while i < len(st):
        ch = st[i]
        if ch not in [',', "(", ")"]:
            current += ch
        if ch == "!":
            parsed.append([current.strip(), parse(st[i+1:])])
            i = len(st)
            current = ""
        if ch == "(":
            substr = ""
            count = 1
            while count != 0:
                i+=1
                ch1 = st[i]
                if ch1 == "(":
                    count += 1
                if ch1 == ")":
                    count -= 1
                substr += ch1
            substr = substr[:-1]
            parsed.append([current.lower().strip(), parse(substr)])
            current = ""
        if ch == ",":
            if(len(current) > 0):
                parsed.append(current.lower().strip())
            current = ""
        i += 1
    if(len(current) > 0):
        parsed.append(current.lower().strip())    
    return parsed

def replace(replaceDict, cond):
    return map(lambda x: replaceDict[x], cond)

def checkEq(expr1, expr2):
    for i in range(len(expr1)):
        if expr1[i] != expr2[i] and expr1[i] != "_":
            return False
    return True

def eval(expr, state, replaceDict):
    if expr[0] == "!":
        return not eval(expr[1][0], state, replaceDict)
    if expr[0] == "forall":
        replaceDict[expr[1][0]] = "_"
        return eval(expr[1][1], state, replaceDict)
    else:
        if expr[0] not in state:
                return False
        for s in state[expr[0]]: 
            if checkEq(replace(replaceDict, expr[1]), s):
                return True
        return False


def do(action, state, effect, parsed=False):
    if not parsed:
        action = parse(action)[0]
    params = action[1]
    action = action[0]
    state = copy.deepcopy(state)
    for e in effect[action]:
        #print effect[action], params
        replaceDict = {'s' : 's'}
        for i in range(len(e[1][1])):
            replaceDict[e[1][1][i]] = params[i]
        
        newParams = replace(replaceDict, e[3])

        if e[0]:
            if e[2] in state:
                for i in range(len(state[e[2]])):
                    if checkEq(newParams, state[e[2]][i]):
                        del state[e[2]][i]
                        break
        else:
            if e[2] not in state:
                state[e[2]] = []
            state[e[2]].append(newParams)

    return state

def rec(conds, state, replaceDicts, negate=False):
    if len(conds) == 0:
        return replaceDicts

    curr = conds[0]
    action = curr[0]
    
    if action == 'forall':
        newReplaceDicts = []
        
        for r in replaceDicts:
            r [curr[1][0]] = ""
            newReplaceDicts.append(r)

        
        result = rec(curr[1][1] + conds[1:], state, newReplaceDicts)

        for r in result:
            r.pop(curr[1][0])
        
        return result

    if action == 'exists':
        
        result = rec(curr[1][1] + conds[1:], state, replaceDicts)

        return result

    if action == '!':
        newConds = conds[1:]
        newConds[0] = newConds[0][0]
        result = rec(newConds, state, replaceDicts, negate=True)
        return result

    actionVars = curr[1]
    newReplaceDicts = []
    if action in state:

        if len(state[action]) == 0 and negate:
            return rec(conds[1:], state, replaceDicts)

        for binding in state[action]:            
            for replaceDict in replaceDicts:
                newRep = copy.copy(replaceDict)
                success = True
                
                for i in range(len(binding)):
                    if actionVars[i] not in newRep:
                        newRep[actionVars[i]] = binding[i]

                    if newRep[actionVars[i]] != binding[i]:
                        if newRep[actionVars[i]] == "":
                            pass
                        else:
                            success = False
                if (success ^ negate):
                    newReplaceDicts.append(newRep)

    return rec(conds[1:], state, newReplaceDicts)
    
def get_all_vars(state):
    var = set()
    for s in state:
        for v in state[s]:
            for x in v:
                var.add(x)

    return var

def all_possible(state, precond):
    possible = []
    all_var = get_all_vars(state)
    for p in precond:
        action =  precond[p][0]
        conds = precond[p][1]
        replaceDicts = [{}]
        replaceDicts = rec(conds, state, replaceDicts)
        for var in action[0][1]:
            if len(replaceDicts) >0 and var not in replaceDicts[0]:
                temp = []
                for replaceDict in replaceDicts:
                    for v in all_var:
                        if v not in replaceDict:
                            newReplaceDict = copy.copy(replaceDict)
                            newReplaceDict[var] = v
                            temp.append(newReplaceDict)
                replaceDicts = temp



        for replaceDict in replaceDicts:    
            newAction = copy.deepcopy(action)
            newVars = newAction[0][1]
            newVars = map(lambda y: y if y not in replaceDict else replaceDict[y], newVars)
            newAction[0][1] = newVars
            possible.append(newAction)

    return possible
        
        ## for cond in conds:
        #     print cond[0]
        #     print cond[1]
        # print "________________________________"

    


def possible(action, state, precond):
    action = parse(action)
    if action[0][0] in precond:
        cond = precond[action[0][0]]
        conds = cond[1]
        replaceDict = {}
        for i in range(len(cond[0][0][1])):
            replaceDict[cond[0][0][1][i]] = action[0][1][i]
        result = rec(conds, state, [replaceDict])
        return len(result)>0

def treesearch(goal, state, precond, effect, actions, depth):
    if goal[0][1] in state[goal[0][0]]:
        return actions

    if depth == 0:
        return None

    poss_actions = all_possible(state, precond)
    bestPlan = None
    for action in poss_actions:
        
        newState = do(action[0], state, effect, True)
        # print actions + [action[0]]
        # print  newState
        # print "==========================================================================="

        plan = treesearch(goal, newState, precond, effect, actions + [action[0]], depth - 1)        
        if plan is not None:
            if bestPlan is None: 
                bestPlan = plan
            elif len(bestPlan) > len(plan):
                bestPlan = plan
    return bestPlan


def achieve(action, state, precond, effect):
    action = parse(action)
    actions  = []
    for depth in range(1, 10):
        print "Starting depth ", depth
        plan = treesearch(action, state, precond, effect, actions, depth)
        if plan is not None:
            return plan
    return None




state = {}
for line in initialFile.readlines():
    s = parse(line.strip())[0]
    if s[0] not in state:
        state[s[0]] = []
    state[s[0]].append(s[1])



precondFile = open('precond.txt')

precond = {}
for line in precondFile.readlines():
    parts = line.split(' :- ')
    action = parts[0]
    action = parse(action)[0][1]
    conds = parts[1]
    conds = parse(conds.strip())
    precond[action[0][0]] = (action, conds)


effectFile = open('effect.txt')

effect = {}
for line in effectFile.readlines():
    if line[0] != '#':
        p = parse(line.strip())[0]
        negate = False
        if p[0] == '!':
            negate = True
            p = p[1:][0][0]
        result = p[0]
        resultParams = p[1][:-1]+["s"]
        action = p[1][-1][1][0]
        if action[0] not in effect:
            effect[action[0]] = []
        effect[action[0]].append((negate, action, result, resultParams))


# print parse("pickup(r, c)") 

# print do("drop(r, c)", state, effect)
# print do("drop(r, a)", state, effect)

#print possible("pickup(r1, x)", state, precond)
# newState =  do("walk(r, q)", state, effect)
# print all_possible(newState, precond)
# newState = do("drop(r1, a)", state, effect)
#print newState 
## print "++++++++++++++++++++++++++++++++++"
# print all_possible(newState, precond)
#print achieve("nextto(r, r1, s)", state, precond, effect)
print len(all_possible(state, precond))
# print state
# print possible("drop(r1, x)", state, precond)
# print possible("drop(r1, a)", state, precond)

# print "++++++++++++++++++++++++++++++++++"
# print newState
# print possible("pickup(r, c)", newState, precond)