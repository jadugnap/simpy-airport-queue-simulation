"""
https://simpy.readthedocs.io/en/latest/examples/carwash.html
Carwash example.

Covers:

- Waiting for other processes
- Resources: Resource

Scenario:
  A carwash has a limited number of washing machines and defines
  a washing processes that takes some (random) time.

  Car processes arrive at the carwash at a random time. If one washing
  machine is available, they start the washing process and wait for it
  to finish. If not, they wait until they an use one.

"""
import random

import simpy


RANDOM_SEED = 42
NUM_WASH_MACHINES = 2       # Number of washing machines in the carwash
NUM_WAX_MACHINES = 2        # Number of waxing machines in the carwash
MEAN_WASHTIME = 7.5         # Average minutes of washing time (exponential distribution)
WAXTIME_PARAMS = [5, 10]    # Limits for uniform distribution of waxing time
T_INTERARRIVAL = 0.5        # Exponential distribution with mean ~0.5 minute
SIM_TIME = 60               # Simulation time in minutes


class Carwash(object):
    """A carwash has a limited number of machines (``NUM_WASH_MACHINES``) to
    clean cars in parallel.

    Cars have to request one of the machines. When they got one, they
    can start the washing processes and wait for it to finish (which
    takes ``washtime`` minutes).

    """
    def __init__(self,
                env,
                num_wash_machines,
                num_wax_machines,
                mean_washtime,
                waxtime_params):
        self.env = env
        self.wash_machine = simpy.Resource(env, num_wash_machines)
        self.wax_machine = simpy.Resource(env, num_wax_machines)
        self.mean_washtime = mean_washtime
        self.waxtime_params = waxtime_params

    def wash(self, car):
        """The washing processes. It takes a ``car`` processes and tries
        to clean it."""
        # random.expovariate takes lambd = 1/mean 
        # Returned values range from 0 to positive infinity if lambd is positive,
        # and from negative infinity to 0 if lambd is negative.
        rand_wash_time = random.expovariate(1 / self.mean_washtime)
        yield self.env.timeout(rand_wash_time)
        print("Washed {} in {} minutes." .format(car, round(rand_wash_time, 2)))
    

    def wax(self, car):
        """The waxing processes after-wash. It takes a ``car`` processes and tries
        to wax it."""
        rand_wax_time = random.uniform( self.waxtime_params[0],
                                        self.waxtime_params[1])
        yield self.env.timeout(rand_wax_time)
        print("Waxed {} in {} minutes." .format(car, round(rand_wax_time, 2)))


def car(env, name, cw):
    """The car process (each car has a ``name``) arrives at the carwash
    (``cw``) and requests a washing machine.

    It starts the washing process and waits for it to finish.

    After washing, car requests a waxing machine.
    Then it starts the waxing process and waits for it to finish.

    Then car leaves the carwash system.
    """
    print('{} arrives at the carwash at {} minutes'.format(name, round(env.now,2)))

    with cw.wash_machine.request() as wash_request:
        yield wash_request

        print('{} enters the wash machine at {} minutes'.format(name, round(env.now,2)))
        yield env.process(cw.wash(name))

        print('{} leaves the wash machine at {} minutes'.format(name, round(env.now,2)))
    
    with cw.wax_machine.request() as wax_request:
        yield wax_request

        print('{} enters the wax machine at {} minutes'.format(name, round(env.now,2)))
        yield env.process(cw.wax(name))

        print('{} leaves the wax machine & carwash at {} minutes\n'.format(name, round(env.now,2)))


def setup(env,
            num_wash_machines,
            num_wax_machines,
            mean_washtime,
            waxtime_params,
            t_inter):
    """Create a carwash, a number of initial cars and keep creating cars
    approx. every ``t_inter`` minutes."""
    # Create the carwash
    carwash = Carwash(env,
                        num_wash_machines,
                        num_wax_machines,
                        mean_washtime,
                        waxtime_params)

    # Initialize first car ID
    i = 0
    
    # Create more cars while the simulation is running
    while True:
        # random.expovariate takes lambd = 1/mean 
        yield env.timeout(random.expovariate(1 / t_inter))
        i += 1
        env.process(car(env, 'Car {}'.format(i), carwash))


# Setup and start the simulation
print('Carwash in action..!!')
random.seed(RANDOM_SEED)  # This helps reproducing the results

# Create an environment and start the setup process
env = simpy.Environment()
env.process(setup(env,
                    NUM_WASH_MACHINES,
                    NUM_WAX_MACHINES,
                    MEAN_WASHTIME,
                    WAXTIME_PARAMS,
                    T_INTERARRIVAL))

# Execute!
env.run(until=SIM_TIME)
