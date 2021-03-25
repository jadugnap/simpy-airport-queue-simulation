import random

import simpy


RANDOM_SEED = 42
NUM_BOARDINGPASS_QUEUES = 2     # Number of BOARDINGPASS_QUEUES in the airport
NUM_SCANNER_QUEUES = 2          # Number of SCANNER_QUEUES in the airport
MEAN_BOARDINGPASS_TIME = 7.5    # Average minutes of boardingpass checking time (exponential distribution)
SCANNER_PARAMS = [5, 10]        # Limits for uniform distribution of scanning time
T_INTERARRIVAL = 0.5            # Exponential distribution with mean ~0.5 minute
SIM_TIME = 60                   # Simulation time in minutes


class Airport(object):
    def __init__(self,
                env,
                num_boardingpass_queues,
                num_scanner_queues,
                mean_boardingpass_time,
                scanner_params):
        self.env = env
        self.boardingpass_queue = simpy.Resource(env, num_boardingpass_queues)
        self.scanner_queue = simpy.Resource(env, num_scanner_queues)
        self.mean_boardingpass_time = mean_boardingpass_time
        self.scanner_params = scanner_params

    def check_boardingpass(self, passenger):
        # random.expovariate takes lambd = 1/mean 
        # Returned values range from 0 to positive infinity if lambd is positive,
        # and from negative infinity to 0 if lambd is negative.
        rand_check_bp_time = random.expovariate(1 / self.mean_boardingpass_time)
        yield self.env.timeout(rand_check_bp_time)
        print("Check boarding pass {} in {} minutes." .format(passenger, round(rand_check_bp_time, 2)))
    

    def check_scanning(self, passenger):
        rand_scanning_time = random.uniform(self.scanner_params[0],
                                            self.scanner_params[1])
        yield self.env.timeout(rand_scanning_time)
        print("Scanning {} in {} minutes." .format(passenger, round(rand_scanning_time, 2)))


def passenger(env, name, ap):
    """The passenger process (each passenger has a ``name``) arrives at the airport
    (``ap``) and requests a boardingpass checking queue.

    It starts the boardingpass checking process and waits for it to finish.

    After boardingpass checking, passenger requests a scanning machine.
    Then it starts the scanning process and waits for it to finish.

    Then passenger leaves the airport system.
    """
    print('{} arrives at the airport at {} minutes'.format(name, round(env.now,2)))

    with ap.boardingpass_queue.request() as bp_check_request:
        yield bp_check_request

        print('{} enters the boardingpass checking process at {} minutes'.format(name, round(env.now,2)))
        yield env.process(ap.check_boardingpass(name))

        print('{} leaves the boardingpass checking process at {} minutes'.format(name, round(env.now,2)))
    
    with ap.scanner_queue.request() as scan_request:
        yield scan_request

        print('{} enters the scanning process at {} minutes'.format(name, round(env.now,2)))
        yield env.process(ap.check_scanning(name))

        print('{} leaves the scanning process & airport at {} minutes\n'.format(name, round(env.now,2)))


def setup(env,
            num_boardingpass_queues,
            num_scanner_queues,
            mean_boardingpass_time,
            scanner_params,
            t_inter):
    """Create an airport, a number of initial passengers and keep creating passengers
    approx. every ``t_inter`` minutes."""
    # Create the airport
    airport = Airport(env,
                        num_boardingpass_queues,
                        num_scanner_queues,
                        mean_boardingpass_time,
                        scanner_params)

    # Initialize first passenger ID
    i = 0
    
    # Create more passengers while the simulation is running
    while True:
        # random.expovariate takes lambd = 1/mean 
        yield env.timeout(random.expovariate(1 / t_inter))
        i += 1
        env.process(passenger(env, 'Passenger {}'.format(i), airport))


# Setup and start the simulation
print('Airport in action..!!')
random.seed(RANDOM_SEED)  # This helps reproducing the results

# Create an environment and start the setup process
env = simpy.Environment()
env.process(setup(env,
                    NUM_BOARDINGPASS_QUEUES,
                    NUM_SCANNER_QUEUES,
                    MEAN_BOARDINGPASS_TIME,
                    SCANNER_PARAMS,
                    T_INTERARRIVAL))

# Execute!
env.run(until=SIM_TIME)
