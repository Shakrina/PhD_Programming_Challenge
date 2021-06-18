from marketsim import MarketSim

# create a new market simulation real market data
market = MarketSim(fin='data/input_dummy.csv', fout='data/output_dummy.csv')

# add agents to the market
market.add_agent(uid='1', tech='gas', cap=4000, var_cost=45)
market.add_agent(uid='2', tech='hydro', cap=6000, var_cost=7)
market.add_agent(uid='3', tech='wind', cap=3300, var_cost=4)
market.add_agent(uid='4', tech='solar', cap=1500, var_cost=1)
market.add_agent(uid='5', tech='storage', cap=100, var_cost=10, storage=400)

# run the market simulation for every timestamp in the input file and save results to the output file
market.run()

