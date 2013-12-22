import rg
import random

#{
#    # a dictionary of all robots on the field mapped
#    # by {location: robot}
#    'robots': {
#        (x1, y1): {   
#            'location': (x1, y1),
#            'hp': hp,
#            'player_id': player_id,
#        },
#
#        # ...and the rest of the robots
#    },
#
#    # number of turns passed (starts at 0)
#    'turn': turn
#}

class Robot:

    def __init__(self):
        self.turn = -1

    def parse(self, game):
        # self.location
        # self.player_id
        # self.hp
        self.loc    = self.location
        self.locX   = self.location[0]
        self.locY   = self.location[1]
        self.game   = game

        if self.turn != game['turn']:
            self.turn   = game['turn']
            self.robots = game['robots']
            self.scores = {} # location score cache

    def log(self, message):
        print "{0}: {1}".format(self.loc, message)



    # Is / can ######################################################

    def is_occupied(self, loc):
        for l in self.robots:
            if self.robots[l]['location'] == loc:
                return True

        return False

    def is_loc_type_ok(self, loc):
        loc_types = rg.loc_types(loc)
        bad_types = ['invalid', 'obstacle']

        for loc_type in loc_types:
            if loc_type in bad_types:
                return False

        return True

    def has_ally_neighbor(self, loc):
        allies = self.get_neighboring_allies(loc)
        allies = [r for r in allies if r['location'] != self.location]

        return len(allies) > 0

    def can_move_to(self, loc):
        return \
            self.is_loc_type_ok(loc)  and \
            not self.is_occupied(loc)

    def can_escape(self):
        outs    = self.get_available_neighbor_locations()
        enemies = len(self.get_neighboring_enemies())

        for out in outs:
            is_better = len(self.get_neighboring_enemies(out)) < enemies
            if is_better:
                return True

        return False

    def is_enemy(self, robot):
        return robot['player_id'] != self.player_id

    def is_ally(self, robot):
        return robot['player_id'] == self.player_id

    def is_near_enemy(self):
        return len(self.get_neighboring_enemies()) > 0

    def is_outnumbered(self):
        allies  = self.get_neighboring_allies()
        enemies = self.get_neighboring_enemies()

        # TODO: consider each enemys number of allies
        
        return len(enemies) > len(allies) + 1

    def is_panic(self):
        enemies = len(self.get_neighboring_enemies())
        allies  = len(self.get_neighboring_allies())

        return allies < enemies and self.hp < 10 * enemies

    def is_open_enemies(self):
        return len(self.get_enemy_openings()) > 0

    def is_someone_fighting(self):
        return len(self.get_fight_openings()) > 0

    def is_in_spawn_area(self):
        return 'spawn' in rg.loc_types(self.loc)

    def is_empty(self, loc):
        return loc not in self.robots



    # Getters #######################################################

    def get_fight_openings(self):
        enemies  = self.get_enemies()
        openings = []

        for enemy in enemies:
            e_loc  = enemy['location']
            allies = self.get_neighboring_allies(e_loc)

            if len(allies) == 0: continue

            locs = self.get_available_neighbor_locations(e_loc)

            for loc in locs:
                if not loc in openings:
                    openings.append(loc)

        return openings

    def get_nearest_fight_opening(self):
        locs = self.get_fight_openings()

        locs.sort(key=lambda l: rg.dist(l, self.loc))
        return locs[0]

    def get_enemy_openings(self):
        enemies  = self.get_enemies()
        openings = []

        for enemy in enemies:
            e_loc = enemy['location']
            locs  = self.get_available_neighbor_locations(e_loc)

            for loc in locs:
                if not loc in openings:
                    openings.append(loc)

        return openings

    def get_nearest_enemy_opening(self):
        locs = self.get_enemy_openings()

        locs.sort(key=lambda l: rg.dist(l, self.loc))

        return locs[0]

    def get_neighbor_locations(self, loc=None):
        loc = loc or self.loc
        x   = loc[0]
        y   = loc[1]
        ls  = [(x-1, y), (x, y-1), (x, y+1), (x+1, y)]

        return [l for l in ls if 0 <= l[0] < 19 and 0 <= l[1] < 19]

    def get_neighbors(self, loc=None):
        rs = self.robots
        return [rs[(x,y)] for x, y in self.get_neighbor_locations(loc) if (x,y) in rs]

    def get_available_neighbor_locations(self, loc=None):
        ls = self.get_neighbor_locations(loc)
        return [l for l in ls if self.can_move_to(l)]

    def get_occupied_neighbors(self, loc=None):
        return [r for r in self.get_neighbors(loc) if r]

    def get_neighboring_enemies(self, loc=None):
        ns = self.get_occupied_neighbors(loc)
        return [r for r in ns if self.is_enemy(r)]

    def get_neighboring_allies(self, loc=None):
        ns = self.get_occupied_neighbors(loc)
        return [r for r in ns if self.is_ally(r)]

    def get_enemies(self):
        robots = [self.robots[loc] for loc in self.robots]
        return [r for r in robots if self.is_enemy(r)]

    def get_allies(self):
        robots = [self.robots[loc] for loc in self.robots]
        return [r for r in robots if self.is_ally(r)]

    def get_nearest_enemy(self):
        enemies = self.get_enemies()

        for enemy in enemies:
            enemy['distance'] = rg.dist(enemy['location'], self.loc)

        enemies.sort(key=lambda e: e['distance'])

        return enemies[0]
 


    # RobotGame actions #############################################

    def guard(self):
        return ['guard']

    def suicide(self):
        return ['suicide']

    def move(self, loc):
        self.robots[loc] = self.robots[self.loc]
        del self.robots[self.loc]
        return ['move', loc]

    def attack(self, loc):
        return ['attack', loc]



    # Low level actions #############################################

    def move_to(self, loc):
        if self.can_move_to(loc):
            return self.move(loc)

        alternatives = self.get_available_neighbor_locations()
        
        if len(alternatives) > 0:
            rnd = random.randint(0, len(alternatives)-1)
            loc = alternatives[rnd]

            if self.can_move_to(loc):
                return self.move(loc)

        return self.guard()

    def move_toward(self, loc):
        loc = rg.toward(self.loc, loc)

        return self.move_to(loc)



    # High level actions ############################################

    def move_to_nearest_enemy(self):
        enemy = self.get_nearest_enemy()
        loc   = enemy['location']

        self.log("Moving to nearest enemy at {0}".format(loc))
        return self.move_toward(loc)

    def move_to_nearest_enemy_opening(self):
        loc = self.get_nearest_enemy_opening()

        self.log("Moving to nearest enemy opening at {0}".format(loc))
        return self.move_toward(loc)

    def move_to_nearest_fight_opening(self):
        loc = self.get_nearest_fight_opening()

        self.log("Moving to nearest fight opening at {0}".format(loc))
        return self.move_toward(loc)

    def attack_weakest_enemy(self):
        enemies = self.get_neighboring_enemies()
        enemies.sort(key=lambda e: e['hp'])
        loc = enemies[0]['location']

        self.log("Fighting enemy at {0}".format(loc))
        return self.attack(loc)

    def flee(self):
        outs = self.get_available_neighbor_locations()

        if len(outs) == 0:
            return self.guard()

        outs.sort(key=lambda l: len(self.get_neighboring_enemies(l))*10 + random.randint(0, 9))

        self.log("Fleeing to {0}".format(outs[0]))
        return self.move(outs[0])



    # Main ##########################################################

    def act(self, game):
        self.parse(game)

        if self.is_in_spawn_area():
            return self.flee()

        if self.is_near_enemy():
            if self.is_panic():
                return self.suicide()
            
            elif self.is_outnumbered() and self.can_escape():
                return self.flee()
            
            else:
                return self.attack_weakest_enemy()

        if self.is_someone_fighting():
            return self.move_to_nearest_fight_opening()

        if self.is_open_enemies():
            return self.move_to_nearest_enemy_opening()

        return self.guard()
