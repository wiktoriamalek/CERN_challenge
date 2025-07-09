import asyncio

from plc.plc_simulator import PLCSimulator

async def main():
    simulator = PLCSimulator(port=4840)
    await simulator.main()
if __name__ == "__main__":
    asyncio.run(main())

