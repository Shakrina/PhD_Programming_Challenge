import csv
from gekko import GEKKO

m = GEKKO()  # Initialize gekko
m.options.SOLVER = 1  # APOPT is an MINLP solver

# optional solver settings with APOPT
m.solver_options = ['minlp_maximum_iterations 500', \
                    # minlp iterations with integer solution
                    'minlp_max_iter_with_int_sol 10', \
                    # treat minlp as nlp
                    'minlp_as_nlp 0', \
                    # nlp sub-problem max iterations
                    'nlp_maximum_iterations 50', \
                    # 1 = depth first, 2 = breadth first
                    'minlp_branch_method 1', \
                    # maximum deviation from whole number
                    'minlp_integer_tol 0.05', \
                    # covergence tolerance
                    'minlp_gap_tol 0.01']


class MarketSim:
    def __init__(self, fin, fout):
        self.times = []
        self.fin = fin
        self.fout = fout
        self.demands = []
        self.hydro_avail = []
        self.solar_avail = []
        self.wind_avail = []
        self.agents = []
        self.storage_cap = 0
        self.storage = 0
        self.storage_bid = 0
        self.market_price = []
        self.cap_buy = []
        self.cap_sell = []
        self.begin = 0
        self.end = 96
        self.soc_initial = 0
        self.market_price = []
        self.system_cost = []
        self.last_cap = []
        self.last_cost = []
        self.hydro_total_cost = []
        self.wind_total_cost = []
        self.solar_total_cost = []
        self.gas_total_cost = []
        self.storage_profit = []

    def read(self):
        with open(self.fin, 'r') as inp:
            csv_reader = csv.reader(inp, delimiter=";")
            next(csv_reader)
            for row in csv_reader:
                self.times.append(row[0])
                self.demands.append(row[1])
                self.hydro_avail.append(row[2])
                self.solar_avail.append(row[3])
                self.wind_avail.append(row[4])

    def add_agent(self, uid, tech, cap, var_cost, **kwargs):
        storage = kwargs.get('storage', None)
        new_agent = {'uid': uid,
                     'tech': tech,
                     'cap': cap,
                     'var_cost': var_cost,
                     'storage': storage}
        if new_agent['tech'] == 'storage':
            self.storage_cap = new_agent['cap']
            self.storage = new_agent['storage']
            self.storage_bid = new_agent['var_cost']
        self.agents.append(new_agent)

    def run(self):
        self.read()

        agents_sort = sorted(self.agents, key=lambda k: k['var_cost'])
        system_cost = 0
        for i, demand in enumerate(self.demands):
            capacity = 0
            for agent in agents_sort:
                if agent['tech'] == 'storage':
                    capacity += 0
                if agent['tech'] == 'solar':
                    capacity += int(agent['cap'] * float(self.solar_avail[i]))
                    system_cost += agent['cap'] * float(agent['var_cost'])
                elif agent['tech'] == 'hydro':
                    capacity += int(agent['cap'] * float(self.hydro_avail[i]))
                    system_cost += agent['cap'] * float(agent['var_cost'])
                elif agent['tech'] == 'wind':
                    capacity += int(agent['cap'] * float(self.wind_avail[i]))
                    system_cost += agent['cap'] * float(agent['var_cost'])
                else:
                    capacity += int(agent['cap'])
                    system_cost += agent['cap'] * float(agent['var_cost']) + 0.5 * 50 * capacity

                if capacity >= int(demand):
                    self.market_price.append(agent['var_cost'])
                    self.last_cap.append(agent['cap'])
                    self.last_cost.append(agent['var_cost'])
                    self.system_cost.append(system_cost)
                    break
            self.cap_buy.append(capacity - int(self.demands[i]))
            if (capacity - self.cap_buy[i]) > self.storage_cap:
                self.cap_sell.append(self.storage_cap)
            else:
                self.cap_sell.append(capacity - self.cap_buy[i])

        days = int(len(self.demands) / 96)
        for day in range(0, days):
            self.calculate()
            self.begin += 96
            self.end += 96
        self.write()

    def calculate(self):
        pow_sold = {}
        pow_bought = {}
        state_of_charge = {}
        bidding_price = {}
        buy_or_sell = {}
        obj = 0

        for i in range(self.begin, self.end):
            # this is analogous to s1, s2, etc
            pow_sold["s{0}".format(i)] = m.Var(value=1, lb=0, ub=self.cap_sell[i])
            # this is analogous to b1, b2, etc
            pow_bought["b{0}".format(i)] = m.Var(value=1, lb=0, ub=self.cap_buy[i])
            # bidding price
            bidding_price["p{0}".format(i)] = m.Var(value=1, lb=self.storage_bid)
            # State of Charge
            state_of_charge["SoC{0}".format(i)] = m.Var(value=1, lb=0, ub=self.storage)
            # Boolean to determine whether we buy or sell
            buy_or_sell["sell{0}".format(i)] = m.Var(value=1, lb=0, ub=1, integer=True)
        for i in range(self.begin, self.end):
            # equations
            # 0.9 is fixed from given
            m.Equation(
                state_of_charge["SoC{0}".format(i)] - self.soc_initial - pow_bought["b{0}".format(i)] * 0.9 + pow_sold[
                    "s{0}".format(i)] / 0.9 == 0)
            self.soc_initial = state_of_charge["SoC{0}".format(i)]

            m.Equation(pow_sold["s{0}".format(i)] <= self.cap_sell[i] * buy_or_sell["sell{0}".format(i)])

            m.Equation(pow_bought["b{0}".format(i)] <= self.cap_buy[i] * (1 - buy_or_sell["sell{0}".format(i)]))

            obj += pow_sold["s{0}".format(i)] * self.market_price[i] - pow_sold["s{0}".format(i)] * bidding_price[
                "p{0}".format(i)] - pow_bought["b{0}".format(i)] * self.market_price[i]
        m.Obj(-obj)
        m.solve(disp=False)

    def write(self, pow_sold, pow_bought):
        # To write to csv output
        # The columns for times and market prices were already found and could be
        # easily written out to a csv file. As for system cost, below is a proposed way
        # to calculate it. Profits of each unit can also be found (please refer to the ReadMe file
        # for formulas). I unfortunately ran out of time to code it.
        for i in range(0, len(self.demands)):
            self.system_cost[i] = self.system_cost[i] - pow_sold[
                "s{0}".format(i)].Value * (self.last_cost[i] - self.storage_bid) + pow_bought[
                                      "b{0}".format(i)].Value * self.last_cost[i]
