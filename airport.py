import random

import simpy

DEBUG_MODE_ENABLED = False # True

RANDOM_SEED = 42
MEAN_BOARDINGPASS_TIME = 0.75   # Exponential service time with mean rate 0.75 minutes
SCANNER_PARAMS = [0.5, 1]       # Uniformly distributed between 0.5 and 1 minute
T_INTERARRIVAL = 0.02            # Mean interarrival rate of 1 passenger per 0.02 minutes, or 50 passengers per minute
SIM_TIME = 60                  # Simulation time in minutes

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
        if DEBUG_MODE_ENABLED:
            print("Check boarding pass {} in {} minutes." .format(passenger, round(rand_check_bp_time, 2)))
    

    def check_scanning(self, passenger):
        rand_scanning_time = random.uniform(self.scanner_params[0],
                                            self.scanner_params[1])
        yield self.env.timeout(rand_scanning_time)
        if DEBUG_MODE_ENABLED:
            print("Scanning {} in {} minutes." .format(passenger, round(rand_scanning_time, 2)))


def passenger(env, name, ap):
    """The passenger process (each passenger has a ``name``) arrives at the airport
    (``ap``) and requests a boardingpass checking queue.

    It starts the boardingpass checking process and waits for it to finish.

    After boardingpass checking, passenger requests a scanning machine.
    Then it starts the scanning process and waits for it to finish.

    Then passenger leaves the airport system.
    """    
    global total_wait_time
    global total_passenger_count
    
    if DEBUG_MODE_ENABLED:
        print('{} arrives at the airport at {} minutes'.format(name, round(env.now,2)))

    with ap.boardingpass_queue.request() as bp_check_request:
        bp_start_wait_time = env.now
        yield bp_check_request

        total_wait_time += (env.now - bp_start_wait_time)
        if DEBUG_MODE_ENABLED:
            print('{} enters the boardingpass checking process at {} minutes'.format(name, round(env.now,2)))
            print('{} total_wait_time due to {} wait for boardingpass checking\n'.format(total_wait_time, name))

        yield env.process(ap.check_boardingpass(name))

        if DEBUG_MODE_ENABLED:
            print('{} leaves the boardingpass checking process at {} minutes'.format(name, round(env.now,2)))
    
    with ap.scanner_queue.request() as scan_request:
        scan_start_wait_time = env.now
        yield scan_request

        total_wait_time += (env.now - scan_start_wait_time)
        if DEBUG_MODE_ENABLED:
            print('{} enters the scanning process at {} minutes'.format(name, round(env.now,2)))
            print('{} total_wait_time due to {} wait for scanning\n'.format(total_wait_time, name))

        yield env.process(ap.check_scanning(name))

        total_passenger_count += 1
        if DEBUG_MODE_ENABLED:
            print('{} leaves the scanning process & airport at {} minutes\n'.format(name, round(env.now,2)))
            print('{} total_passenger_count\n'.format(total_passenger_count))


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
print('Airport in action..!!\n')
random.seed(RANDOM_SEED)  # This helps reproducing the results

for bp_queue in range(18,22):
    for scan_queue in range(18,22):
        total_wait_time = 0
        total_passenger_count = 0

        # Create an environment and start the setup process
        env = simpy.Environment()
        env.process(setup(env,
                        num_boardingpass_queues=bp_queue,
                        num_scanner_queues=scan_queue,
                        mean_boardingpass_time=MEAN_BOARDINGPASS_TIME,
                        scanner_params=SCANNER_PARAMS,
                        t_inter=T_INTERARRIVAL))

        # Execute!
        env.run(until=SIM_TIME)

        avg_wait_time = round(total_wait_time / total_passenger_count, 2)
        print("avg_wait_time is {} minutes with\n- {} minutes of total_wait_time,\n- {} total_passenger_count,\n- {} lines of boardingpass queue, and\n- {} lines of scanner queue.\n".format(
            avg_wait_time, total_wait_time, total_passenger_count, bp_queue, scan_queue))
