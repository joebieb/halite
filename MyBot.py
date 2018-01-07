import hlt
import logging
from collections import OrderedDict

# GAME START
game = hlt.Game("Spoof_v6")
logging.info('Starting my %s bot!', game._name)

def navigate(ship, entity, multiplier = 1):
    navigate_command = ship.navigate(
        ship.closest_point_to(entity),
        game_map,
        speed=int(hlt.constants.MAX_SPEED * multiplier),
        ignore_ships=False)
    if navigate_command:
        command_queue.append(navigate_command)

def kamikazee(ship, entity):
    navigate_command = ship.navigate(
        entity,
        game_map,
        speed=int(hlt.constants.MAX_SPEED),
        ignore_ships=True)
    if navigate_command:
        command_queue.append(navigate_command)

while True:
    # TURN START
    game_map = game.update_map()
    command_queue = []

    me = game_map.get_me()
    enemies = [enemy for enemy in game_map.all_players() if enemy.id != me.id]
    my_ships = me.all_ships()
    my_docked_ships = [ship for ship in my_ships if ship.docking_status != ship.DockingStatus.UNDOCKED]
    #planet_docking_status = []
    enemy_ships = [ship for ship in game_map._all_ships() if ship not in my_ships]
    docked_enemy_ships = [ship for ship in enemy_ships if ship.docking_status != ship.DockingStatus.UNDOCKED]
    unowned_planets = [planet for planet in game_map.all_planets() if not planet.is_owned()]
    my_planets = [planet for planet in game_map.all_planets() if planet.is_owned() and planet.owner.id == me.id]
    enemy_planets = [planet for planet in game_map.all_planets() if planet.is_owned() and planet.owner.id != me.id]
    targeted_planets = []

    # find center of enemy mass
    planet_x = [planet.x for planet in enemy_planets]
    ship_x = [ship.x for ship in enemy_ships]
    planet_y = [planet.y for planet in enemy_planets]
    ship_y = [ship.y for ship in enemy_ships]
    x = planet_x + ship_x
    y = planet_y + ship_y
    enemy_centroid = hlt.entity.Position(0,0)

    if len(x):
        enemy_centroid = hlt.entity.Position(sum(x) / len(x), sum(y) / len(y))

    entities_by_distance_to_enemy_centroid = OrderedDict(sorted(game_map.nearby_entities_by_distance(enemy_centroid).items(), key=lambda t: t[0]))

    my_ships_by_distance_to_enemy_centroid = [entities_by_distance_to_enemy_centroid[distance][0]
                                                for distance in entities_by_distance_to_enemy_centroid
                                                if entities_by_distance_to_enemy_centroid[distance][0] in my_ships
                                                and entities_by_distance_to_enemy_centroid[distance][0] not in my_docked_ships]

    #logging.info(enemy_centroid)
    # find undocked ships that are closest to action and make them fighters first set the rest as miners
    attack_ships = my_ships_by_distance_to_enemy_centroid[0 : int(len(my_ships_by_distance_to_enemy_centroid) * .40)]
    planet_busters = my_ships_by_distance_to_enemy_centroid[int(len(my_ships_by_distance_to_enemy_centroid) * .40): int(len(my_ships_by_distance_to_enemy_centroid) * .90)]

    # For every ship that I control
    for ship in my_ships:
        # If the ship is docked
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            continue

        entities_by_distance = OrderedDict(sorted(game_map.nearby_entities_by_distance(ship).items(), key=lambda t: t[0]))
        target_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in game_map.all_planets() and entities_by_distance[distance][0] not in targeted_planets]
        target_unowned_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in unowned_planets and entities_by_distance[distance][0] not in targeted_planets]
        target_enemy_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in enemy_planets]
        target_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in enemy_ships]
        target_docked_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in docked_enemy_ships]

        # if ship in attack_ships attack
        if ship in attack_ships:
            for enemy_ship in target_ships:
                # if unowned planet is closer, then dock, otherwise attack
                if target_unowned_planets[0]:
                    if ship.calculate_distance_between(target_unowned_planets[0]) < ship.calculate_distance_between(enemy_ship):
                        if ship.can_dock(target_unowned_planets[0]):
                            command_queue.append(ship.dock(target_unowned_planets[0]))
                    else:
                        navigate(ship, enemy_ship, .8)
                else:
                    navigate(ship, enemy_ship, .8)
                break
        elif ship in planet_busters:
            for planet in target_enemy_planets:
                kamikazee(ship, planet)
                break
        else:
            for planet in target_planets:
                # If we can dock, let's (try to) dock. If two ships try to dock at once, neither will be able to.
                if ship.can_dock(planet) and planet in unowned_planets:
                    command_queue.append(ship.dock(planet))
                elif ship.can_dock(planet) and planet in my_planets and not planet.is_full():
                    command_queue.append(ship.dock(planet))
                # if planet is owned then attack
                elif planet.is_owned() and planet in enemy_planets:
                    for enemy_ship in planet.all_docked_ships():
                        navigate(ship, enemy_ship)
                        break
                else:
                    targeted_planets.append(planet)
                    navigate(ship, planet)
                break

    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)
    # TURN END

# GAME END
