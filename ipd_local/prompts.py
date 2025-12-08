single_strategy_prompt = """
# INSTRUCTIONS
You are an expert in Iterated Prisoner's Dilemma strategies. 
You will comprehensively summarize one Iterated Prisoner's Dilemma strategy as text only.
Concrete, mechanistic, parameterized. 
Name thresholds, counters, timers, probabilities.
NO FLUFF, MAKE SURE TO JAM WITH INFO AND BE DESCRIPTIVE.
BANNED: often, usually, generally, tends, might, could, somewhat, kind of.
IMPORTANT: REMEMBER that returning "False" means "cooperate" and returning "True" means "defect"

Return only the description. Do not say anything like, "Here's the description" or anything like that 
- return EXACTLY 40 words, jam pack with information, maintain the same structure of
  - logic of the strategy (what does it start with, what does it do after)
  - archetype of the strategy
  - how it handles certain kinds of opponents that are worthy of note
  - if it is nice or not, retaliating or not, forgiving or not, envious or not{noise_str}

# EXAMPLE

## function:
    if len(othermoves) == 0:
        return False
    if len(othermoves) > 7:
      if othermoves[-1] and not othermoves[-2] and othermoves[-3] and not othermoves[-4] and othermoves[-5] and not othermoves[-6] and othermoves[-7] and not othermoves[-8]:
        return True
#for an alternator
    if len(othermoves) > 7:
      if not othermoves[-1] and othermoves[-2] and not othermoves[-3] and othermoves[-4] and not othermoves[-5] and othermoves[-6] and not othermoves[-7] and othermoves[-8]:
        return True
#for an alternator
    if len(othermoves) > 7:
      if othermoves[-1] and othermoves[-2] and not othermoves[-3] and not othermoves[-4] and othermoves[-5] and othermoves[-6] and not othermoves[-7] and not othermoves[-8]:
        return False
    if len(othermoves) > 8:
      if othermoves[-2] and othermoves[-3] and not othermoves[-4] and not othermoves[-5] and othermoves[-6] and othermoves[-7] and not othermoves[-8] and not othermoves[-9]:
        return False
    if len(othermoves) > 9:
      if othermoves[-3] and othermoves[-4] and not othermoves[-5] and not othermoves[-6] and othermoves[-7] and othermoves[-8] and not othermoves[-9] and not othermoves[-10]:
        return False
#these last three are all if it is against a tit for two tats where it will reset peace with three cooperates in a row
    if len(othermoves) > 4:
      if othermoves [-1] and othermoves [-2] and othermoves [-3] and othermoves [-4]  and othermoves [-5]:
#if they have a nuke for tat this means that if they betrayed for the last five rounds then you should betray as well
        return True
    if len(othermoves) > 4:
      if not othermoves [-1] and not othermoves [-2] and not othermoves [-3] and not othermoves [-4]  and not othermoves [-5]:
#If they have a very forgiving strategy and you keep on cooperating this allows you to betray if they are being too forgiving
        return True
    if len(othermoves) > 0:
      if othermoves [-1] and mymoves [-1]:#if we both betray
        return False
      if othermoves [-1] and not mymoves [-1]: #if they betray and I cooperate
        return True
      if mymoves [-1] and not othermoves[-1]: #if I betray and they cooperate
        return True
#if we both cooperate
    return False

## output: 

Starts cooperating, detects alternator patterns triggering defection, identifies Tit-for-Two-Tats resetting with three cooperations, punishes five consecutive moves, retaliates after exploited, cooperates after mutual defection, nice initially, retaliating, somewhat forgiving, highly exploitative against predictable opponents, handles noise forgiving.

# TASK
Now summarize the following strategy:
{strategy_code}
"""