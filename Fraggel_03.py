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

    def parse(self, game):
        # self.location
        # self.player_id
        # self.hp
        self.loc    = self.location
        self.locX   = self.location[0]
        self.locY   = self.location[1]
        self.game   = game
        self.turn   = game['turn']
        self.robots = game['robots']

        # two dimensional list [x][y] filled with robots or None
        self.matrix = [[None for x in xrange(19)] for y in xrange(19)]

        for robot in self.robots:
            x                 = robot[0]
            y                 = robot[1]
            self.matrix[x][y] = self.robots[robot]

    def log(self, message):
        print "{0}: {1}".format(self.loc, message)



    # Is / can ######################################################

    def can_move_to(self, loc):
        loc_types = rg.loc_types(loc)

        for loc_type in loc_types:
            # loc_type == 'spawn'   or \
            if  loc_type == 'invalid' or \
                loc_type == 'obstacle':
                return False

        return not self.is_occupied(loc)

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

    def is_alone(self):
        return len(self.get_occupied_neighbors()) == 0

    def is_near_enemy(self):
        return len(self.get_neighboring_enemies()) > 0

    def is_outnumbered(self):
        allies  = self.get_neighboring_allies()
        enemies = self.get_neighboring_enemies()
        
        return len(enemies) > len(allies) + 1

    def is_occupied(self, loc):
        if self.loc == loc:
            return True

        neighbors = self.get_occupied_neighbors()
        for r in neighbors:
            if r['location'] == loc:
                return True

        return False

    def is_panic(self):
        enemies = len(self.get_neighboring_enemies())
        allies  = len(self.get_neighboring_allies())

        return allies < enemies and self.hp < 10 * enemies

    def is_open_enemies(self):
        return len(self.get_enemy_openings()) > 0

    def is_someone_fighting(self):
        return len(self.get_fight_openings()) > 0



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

        self.log("Nearest enemy openings: {0}".format(locs))

        return locs[0]

    def get_neighbor_locations(self, loc=None):
        loc = loc or self.loc
        x   = loc[0]
        y   = loc[1]
        ls  = [(x-1, y), (x, y-1), (x, y+1), (x+1, y)]

        return [l for l in ls if 0 <= l[0] < 19 and 0 <= l[1] < 19]

    def get_neighbors(self, loc=None):
        m = self.matrix
        return [m[x][y] for x, y in self.get_neighbor_locations(loc)]

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
 


    # Low level actions #############################################

    def guard(self):
        return ['guard']

    def move_to(self, loc):
        if self.can_move_to(loc):
            return ['move', loc]

        alternatives = self.get_available_neighbor_locations()
        
        if len(alternatives) > 0:
            rnd = random.randint(0, len(alternatives)-1)
            loc = alternatives[rnd]

            if self.can_move_to(loc):
                return ['move', loc]

        return self.guard()

    def move_to_center(self):
        loc = rg.toward(self.loc, rg.CENTER_POINT)

        return self.move_to(loc)

    def move_toward(self, loc):
        loc = rg.toward(self.loc, loc)

        return self.move_to(loc)

    def boom(self):
        return ['suicide']



    # High level actions ############################################

    def move_to_nearest_enemy(self):
        enemy = self.get_nearest_enemy()
        loc   = enemy['location']

        self.log("Moving to nearest enemy at {0}".format(loc))

        return self.move_toward(loc)

    def attack_enemy(self):
        enemies = self.get_neighboring_enemies()
        enemies.sort(key=lambda e: e['hp'])
        loc = enemies[0]['location']

        self.log("Fighting enemy at {0}".format(loc))

        return ['attack', loc]

    def flee(self):
        outs = self.get_available_neighbor_locations()

        outs.sort(key=lambda l: len(self.get_neighboring_enemies(l)))

        self.log("Fleeing to {0}".format(outs[0]))

        return ['move', outs[0]]

    def move_to_nearest_enemy_opening(self):
        loc = self.get_nearest_enemy_opening()

        self.log("Moving to nearest enemy opening at {0}".format(loc))

        return self.move_toward(loc)

    def move_to_nearest_fight_opening(self):
        loc = self.get_nearest_fight_opening()

        self.log("Moving to nearest fight opening at {0}".format(loc))

        return self.move_toward(loc)



    # Main ##########################################################

    def act(self, game):
        self.parse(game)

        if self.is_near_enemy():
            if self.is_panic():
                return self.boom()
            
            elif self.is_outnumbered() and self.can_escape():
                return self.flee()
            
            else:
                return self.attack_enemy()

        elif self.is_someone_fighting():
            return self.move_to_nearest_fight_opening()

        elif self.is_open_enemies():
            return self.move_to_nearest_enemy_opening()

        return self.guard()
