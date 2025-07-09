import asyncio
import pytest
import os
import pytest_asyncio

from plc.plc_client import PLCClient
from plc.plc_simulator import PLCSimulator

SERVER_PORT=4840
SERVER_URL_ALARM = f"opc.tcp://localhost:{SERVER_PORT}/freeopcua/server/"
CLIENT_TIMEOUT = 5  # seconds


@pytest_asyncio.fixture(scope="function")
async def plc() -> PLCClient:
                                                    
    """ Instance of the OPC UA client to communicate with the simulator """
    plc = PLCClient(url=SERVER_URL_ALARM, timeout=CLIENT_TIMEOUT)
    await plc.init()

    # Set initial conditions here:
    # Stop
    await plc.set_object_pulse("DI0") # Pressed START button
    await asyncio.sleep(3)
    # PreFilling
    await plc.set_object_value("DI5", True) # Minimum level is reached
    await plc.set_object_value("DI6", True)
    await asyncio.sleep(3)
    # Ready
    await plc.set_object_pulse("DI4") # First Reset errors for a clean start
    await plc.set_object_pulse("DI1") # Pressed RUN button
    await asyncio.sleep(3)
    # Filling...

    # Yield fixture
    yield plc

    # Disconnect
    await plc.disconnect()

class TestAlarm:


    # Trigger overfilling condition
    @pytest.mark.asyncio
    async def test_fillingheating_overfilling(self, plc: PLCClient):
        # Assert initial conditions
        assert await plc.get_object_value("DQ0") == True # Tank was filling

        # Simulate overfilling condition
        await plc.set_object_value("DI8", True) # Overfilling sensor active
        await asyncio.sleep(1) # Waiting for reactions

        # Assert actuations after overfilling condition
        assert await plc.get_object_value("DQ0") == False # Tank stopped filling
        assert await plc.get_alarm_status("A0") == True # Alarm is triggered
        assert await plc.get_object_value("DQ3") == True # Discharging gate is open

        # Cleanup conditions here:
        await plc.set_object_value("DI8",False)
        await asyncio.sleep(1)
        await plc.set_object_pulse("DI4")
        await asyncio.sleep(1)

        assert await plc.get_alarm_status("A0")==False
        assert await plc.get_object_value("DQ3")==False

    @pytest.mark.asyncio
    async def test_tank_level_too_low(self, plc:PLCClient):
        assert await plc.get_object_value("DQ0")==True
        await plc.set_object_value("DI5",False)
        await asyncio.sleep(1)

        assert await plc.get_alarm_status("A1") == True
        await plc.set_object_value("DI5",True)
        await asyncio.sleep(1)

        await plc.set_object_pulse("DI4")
        await asyncio.sleep(1)

        assert await plc.get_alarm_status("A1")==False

    @pytest.mark.asyncio
    async def test_temperature_too_high(self,plc:PLCClient):
        await plc.set_object_value("AI0",85)
        await asyncio.sleep(1)

        assert await plc.get_alarm_status("A2")==True
        await plc.set_object_value("AI0",45)
        await asyncio.sleep(1)
        await plc.set_object_pulse("DI4")
        await asyncio.sleep(1)
        assert await plc.get_alarm_status("A2")==False

    @pytest.mark.asyncio
    async def test_temperature_too_low(self,plc:PLCClient):
        await plc.set_object_value("AIO",5)
        await asyncio.sleep(1)

        assert await plc.get_alarm_status("A3")==True

        await plc.set_object_value("AI0",45)
        await asyncio.sleep(1)
        await plc.set_object_pulse("DI4")
        await asyncio.sleep(1)

        assert await plc.get_alarm_status("A3")==False

    @pytest.mark.asyncio
    async def test_discharging_door_open(self,plc:PLCClient):
        await plc.set_object_value("DI9",True)
        await asyncio.sleep(1)
        assert await plc.get_alarm_status("A4")==True

        await plc.set_object_value("DI9",False)
        await asyncio.sleep(1)

        await plc.set_object_pulse("DI4")
        await asyncio.sleep(1)

        assert await plc.get_alarm_status("A4")==False

    @pytest.mark.asyncio
    async def test_emergency_button(self,plc:PLCClient):
        await plc.set_object_pulse("DI3")
        await asyncio.sleep(1)

        assert await plc.get_alarm_status("A5")==True

        await plc.set_object_value("DI3",False)
        await asyncio.sleep(1)
        await plc.set_object_pulse("DI4")
        await asyncio.sleep(1)
        assert await plc.get_alarm_status("A5")==False



