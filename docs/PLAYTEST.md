# Play-test checklist

`tests/test_api.py` checks what the server answers, but not whether the Flash
client does the right thing with it. The expansion bug (the zoo grid was drawn
one size too big) only showed up in the real client. Run through this list
after bigger changes, with a fresh account and with an older save.

**Record the traffic.** Open the browser's developer tools on the Network tab
(or use Fiddler/Charles), filter on `ZooApi.php` and keep "preserve log" on.
When something looks wrong, save the request (`json=` form field) and the
response. Those two are what's needed to fix it. Also note the level and
whether the tutorial was running.

For each step, check what the client **shows** and that it is still the same
after a **reload** (F5). A difference after reloading means the server saved
something else than the client showed.

## Start

- [ ] Register, log in, finish the tutorial.
- [ ] Reload: money, XP, level, zoo and inventory are unchanged.

## Building

- [ ] Buy and place a cage, a deco, a road, a store, a trashbin.
- [ ] Buildings next to a road connected to the entrance are active; move a road away and they turn inactive.
- [ ] Finish a building instantly (costs real currency).
- [ ] Move, rotate and sell each kind of item; the money matches the sell price.
- [ ] Put each kind into the inventory and back onto the field.
- [ ] Sell items from the inventory.
- [ ] Buy a zoo expansion before reaching its level; the zoo grows at once.
- [ ] Reach level 10/20/...: the zoo grows for free.
- [ ] Choose another entrance building.

## Animals

- [ ] Buy animals into a cage; a full cage refuses more.
- [ ] Feed, water, clean, cuddle: timers reset, XP and paws go up, food goes down.
- [ ] A sick cage: heal (medicine) and super heal (supermedicine).
- [ ] Super feed and power feed (buy the packs first).
- [ ] Breed (start + end, and instant breed); the baby shows in the cage.
- [ ] Move a baby to the inventory and back into a cage.
- [ ] Put a cage with animals in the inventory and place it again: the animals come back, and their needs are as they were.
- [ ] Upgrade a cage (coins + paws).
- [ ] Collect paw drops and collection items; the paw counter and the collection book go up and stay up after a reload.

## Trash and stores

- [ ] Trash appears on roads and in bins over time; empty a bin and clear road trash.
- [ ] Collect store money and the entrance fee.

## Features

- [ ] Daily quests: start one, do its tasks (the counts go down), collect the reward, abort one, buy new quests.
- [ ] Complete a collection set and take each reward type you can.
- [ ] Hire an assistant, use it (all cages that need it are done), let one run out and refuse the renew popup.
- [ ] Zoo director (all assistants hired).
- [ ] Breeding lab: breed two inventory animals, use an elixir, collect the baby.
- [ ] Nursery: raise the baby, use a raising potion, collect the adult.
- [ ] Fortune wheel: buy a ticket and spin; a resource prize stops at the storage limit.
- [ ] Buy resources in the shop; buying more than fits in storage is refused without charging.

## Things that should fail cleanly

These should show nothing broken: the client's change is undone and the
game keeps working.

- [ ] Buy something you can't afford.
- [ ] Seasonal event windows (answer "event not running").
- [ ] Features that aren't implemented yet (see the README list).
