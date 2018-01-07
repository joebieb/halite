"""
Welcome to your first Halite-II bot!

This bot's name is Settler. It's purpose is simple (don't expect it to win complex games :) ):
1. Initialize game
2. If a ship is not docked and there are unowned planets
2.a. Try to Dock in the planet if close enough
2.b If not, go towards the planet

Note: Please do not place print statements here as they are used to communicate with the Halite engine. If you need
to log anything use the logging module.
"""
# Let's start by importing the Halite Starter Kit so we can interface with the Halite engine
import hlt
# Then let's import the logging module so we can print out information
import logging
from collections import OrderedDict

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("v2")
# Then we print our start message to the logs
logging.info('Starting my %s bot!', game._name)

while True:
    # TURN START
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()

    me = game_map.get_me()
    enemies = [enemy for enemy in game_map.all_players() if enemy.id != me.id]
    my_ships = me.all_ships()
    enemy_ships = [ship for ship in game_map._all_ships() if ship not in my_ships]
    unowned_planets = [planet for planet in game_map.all_planets() if not planet.is_owned()]
    my_planets = [planet for planet in game_map.all_planets() if planet.is_owned() and planet.owner.id == me.id]
    enemy_planets = [planet for planet in game_map.all_planets() if planet.is_owned() and planet.owner.id != me.id]

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []

    targeted_planets = []

    # For every ship that I control
    for ship in my_ships:
        # If the ship is docked
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            continue

        entities_by_distance = OrderedDict(sorted(game_map.nearby_entities_by_distance(ship).items(), key=lambda t: t[0]))
        target_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in unowned_planets and entities_by_distance[distance][0] not in targeted_planets]
        target_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if entities_by_distance[distance][0] in enemy_ships and entities_by_distance[distance][0]]

        for planet in target_planets:
            targeted_planets.append(planet)
            # If we can dock, let's (try to) dock. If two ships try to dock at once, neither will be able to.
            if ship.can_dock(planet):
                # We add the command by appending it to the command_queue
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
