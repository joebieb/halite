import hlt
import logging
from collections import OrderedDict

# GAME START
game = hlt.Game("Spoof_v4")
logging.info('Starting my %s bot!', game._name)

while True:
    # TURN START
    game_map = game.update_map()

    me = game_map.get_me()
    enemies = [enemy for enemy in game_map.all_players() if enemy.id != me.id]
    my_ships = me.all_ships()
    enemy_ships = [ship for ship in game_map._all_ships() if ship not in my_ships]
    docked_enemy_ships = [ship for ship in enemy_ships if ship.docking_status != ship.DockingStatus.UNDOCKED]
    unowned_planets = [planet for planet in game_map.all_planets() if not planet.is_owned()]
    my_planets = [planet for planet in game_map.all_planets() if planet.is_owned() and planet.owner.id == me.id]
    enemy_planets = [planet for planet in game_map.all_planets() if planet.is_owned() and planet.owner.id != me.id]

    command_queue = []

    targeted_planets = []

    # find closest 3rd undocked ships that are closest to action and make them fighters first set the rest as miners

    # For every ship that I control
    for ship in my_ships:
        # If the ship is docked
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            continue

        entities_by_distance = OrderedDict(sorted(game_map.nearby_entities_by_distance(ship).items(), key=lambda t: t[0]))
        target_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in unowned_planets and entities_by_distance[distance][0] not in targeted_planets]
        target_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in docked_enemy_ships]

        if len(target_planets) == 0:
            for enemy_ship in target_ships:
                navigate_command = ship.navigate(
                    ship.closest_point_to(enemy_ship),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    ignore_ships=False)
                if navigate_command:
                    command_queue.append(navigate_command)
                break
        else:
            for planet in target_planets:
                targeted_planets.append(planet)
                # If we can dock, let's (try to) dock. If two ships try to dock at once, neither will be able to.
                if ship.can_dock(planet):
                    command_queue.append(ship.dock(planet))
                else:
                    navigate_command = ship.navigate(
                        ship.closest_point_to(planet),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=True)

                    if navigate_command:
                        command_queue.append(navigate_command)
                break

    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
