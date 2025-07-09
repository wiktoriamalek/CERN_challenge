import os
from operator import truediv

from asyncua import Server, ua
import asyncio

from enum import Enum


# SERVER_URL = f"opc.tcp://localhost:${os.environ.get("OPCUA_SERVER")}/freeopcua/server/"

class PLCStep(Enum):
    STOP = "Stop"
    PREFILL = "Prefill"
    FILL = "Fill"
    HEAT = "Heat"
    DISCHARGE = "Discharge"
    ERROR = "Error"


class PLCSimulator:
    def __init__(self, port, auto_update_inputs=True):
        self.port = port
        self.auto_update_inputs = auto_update_inputs
        # Initialize input/output and alarm registers. Complete the registers with the needed signals
        self.digital_inputs = {
            "DI0": False,
            "DI1": False,
            "DI2": False,
            "DI3": False,
            "DI4": False,
            "DI5": False,
            "DI6": False,
            "DI7": False,
            "DI8": False,
            "DI9": False,
        }
        self.analog_inputs = {"AI0": 22.0}
        self.digital_outputs = {
            "DQ0": False,
            "DQ1": False,
            "DQ2": False,
            "DQ3": False,
        }
        # Alarms have Active, UnAck ("Unacknowledged"), and Status attributes
        #   Active: True if the alarm is active, False otherwise
        #   UnAck: True if the alarm is unacknowledged after it was triggered
        #   Status: True if the alarm is either active or unacknowledged
        self.alarms = {
            "A0": {"Active": False, "UnAck": False, "Status": False},
            "A1": {"Active": False, "UnAck": False, "Status": False},
            "A2": {"Active": False, "UnAck": False, "Status": False},
            "A3": {"Active": False, "UnAck": False, "Status": False},
            "A4": {"Active": False, "UnAck": False, "Status": False},
            "A5": {"Active": False, "UnAck": False, "Status": False}
        }

        # Time interval for cyclic execution (in seconds)

        # Too high of a frequency effectively creates an unbeatable race condition where the database
        # is locked for reading (or rather an old value is read)
        # That's the reason for the change from 0.2s to 0.4s
        self.cycle_time = 0.4
        self.step = PLCStep.STOP
        self.prefill_ready = False

    async def update_inputs(self):
        # Update digital input readings from the OPC UA server
        if self.auto_update_inputs:
            for name in self.digital_inputs.keys():
                myvar = await self.myobj.get_child(f"{self.idx}:{name}")
                value = await myvar.read_value()
                self.digital_inputs.update({name: value})
            # Complete the code to update the analog input readings from the server
            for name in self.analog_inputs.keys():
                myvar = await self.myobj.get_child(f"{self.idx}:{name}")
                value = await myvar.read_value()
                self.analog_inputs.update({name: value})

    async def write_outputs(self):
        # Complete the necessary code to write the output values into the OPC UA server
        for name, val in self.digital_outputs.items():
            myvar = await self.myobj.get_child(f"{self.idx}:{name}")
            await myvar.write_value(val)

    async def set_alarms(self):
        for key, values in self.alarms.items():
            myalarm = await self.myobj.get_child(f"{self.idx}:{key}")
            # If the alarm is active, set UnAck and Status to True
            if values["Active"]:
                values["UnAck"] = True
                values["Status"] = True
            # Write the values to the OPC UA server
            for newkey, value in values.items():
                myvar = await myalarm.get_child(f"{self.idx}:{newkey}")
                await myvar.write_value(value)

    async def reset_alarms(self):
        # Reset all alarms to inactive and acknowledged
        for key in self.alarms.keys():
            self.alarms[key].update({"UnAck": False})
            self.alarms[key].update({"Status": False})
            self.alarms[key].update({"Active": False})

    async def execute_control_logic(self):
        # Initialize variables as needed
        # step = PLCStep.STOP
        # trip = False
        SETPOINT = 45.0
        MAX_TEMPERATURE = 80.0
        MIN_TEMPERATURE = 10.0
        # Add any other necessary variables here

        try:
            while True:
                # Updating inputs from server
                await self.update_inputs()

                self.alarms["A0"]["Active"] = self.digital_inputs["DI8"]
                self.alarms["A1"]["Active"] = self.digital_inputs["DI5"]
                self.alarms["A2"]["Active"] = self.analog_inputs["AI0"] > MAX_TEMPERATURE
                self.alarms["A3"]["Active"] = self.analog_inputs["AI0"] < MIN_TEMPERATURE
                self.alarms["A4"]["Active"] = self.digital_inputs["DI9"]
                self.alarms["A5"]["Active"] = self.digital_inputs["DI3"]

                error_found = any(
                    self.alarms[alarm]["Active"]
                    for alarm in self.alarms
                )
                if error_found and self.step != PLCStep.ERROR:
                    self.step = PLCStep.ERROR

                if self.analog_inputs["AI0"] >= SETPOINT:
                    pass

                # Implement alarm logic
                # (Example) Tank level too high
                self.alarms["A0"]["Active"] = self.digital_inputs["DI8"]
                # Add more alarms here...
                self.alarms["A1"]["Active"] = self.digital_inputs["DI5"]
                self.alarms["A2"]["Active"] = (
                        self.analog_inputs["AI0"] > MAX_TEMPERATURE
                )
                self.alarms["A3"]["Active"] = (
                        self.analog_inputs["AI0"] < MIN_TEMPERATURE
                )
                self.alarms["A4"]["Active"] = self.digital_inputs["DI9"]
                self.alarms["A5"]["Active"] = self.digital_inputs["DI3"]

                error_found = (
                        self.alarms["A0"]["Active"]
                        or self.alarms["A1"]["Active"]
                        or self.alarms["A2"]["Active"]
                        or self.alarms["A3"]["Active"]
                        or self.alarms["A4"]["Active"]
                        or self.alarms["A5"]["Active"]
                )

                if error_found and self.step != PLCStep.ERROR:
                    self.step = PLCStep.ERROR

                if self.digital_inputs["DI4"]:
                    error_found = False
                    if not self.digital_inputs["DI9"]:
                        if self.alarms["A0"]["Active"]:
                            self.step = PLCStep.DISCHARGE
                        elif self.alarms["A1"]["Active"]:
                            self.step = PLCStep.PREFILL
                        elif self.alarms["A2"]["Active"]:
                            self.step = PLCStep.DISCHARGE
                        elif self.alarms["A3"]["Active"]:
                            self.step = PLCStep.HEAT
                        elif self.alarms["A4"]["Active"]:
                            self.step = PLCStep.FILL
                        else:
                            self.step = PLCStep.STOP

                    await self.reset_alarms()

                # Press RESET for ack.

                # Setting alarms register values and update the OPC UA server

                # Implement GRAFCET logic:
                #   This should follow a state machine approach, where each state is defined by the current conditions of the inputs and outputs.
                #   The step and transition logic should be implemented here.
                #   For example, if a certain condition is met, change the step to "Start" or "Stop", etc.

                if self.digital_inputs["DI2"]:
                    self.step = PLCStep.STOP

                if self.step == PLCStep.STOP:
                    if self.digital_inputs["DI0"] and not self.digital_inputs["DI9"]:
                        self.step = PLCStep.PREFILL
                elif self.step == PLCStep.PREFILL:
                    if self.digital_inputs["DI6"]:
                        self.prefill_ready = True
                    if self.digital_inputs["DI1"]:
                        self.step = PLCStep.FILL
                    if self.digital_inputs["DI2"]:
                        self.step = PLCStep.STOP
                elif self.step == PLCStep.FILL:
                    if self.digital_inputs["DI2"]:
                        self.step = PLCStep.STOP
                    elif self.digital_inputs["DI7"]:
                        self.step = PLCStep.HEAT
                elif self.step == PLCStep.HEAT:
                    if self.digital_inputs["DI2"]:
                        self.step = PLCStep.STOP
                    if self.analog_inputs["AI0"] >= SETPOINT:
                        self.step = PLCStep.DISCHARGE
                elif self.step == PLCStep.DISCHARGE:
                    if self.digital_inputs["DI2"]:
                        self.step = PLCStep.STOP
                    if self.digital_inputs["DI6"]:
                        self.step = PLCStep.FILL
                elif self.step == PLCStep.ERROR:
                    pass

                if error_found:
                    if self.alarms["A0"]["Active"]:
                        self.digital_outputs["DQ0"] = False
                        self.digital_outputs["DQ1"] = False
                        self.digital_outputs["DQ2"] = False
                        self.digital_outputs["DQ2"] = False
                        self.digital_outputs["DQ3"] = True
                    elif self.alarms["A1"]["Active"]:
                        self.digital_outputs["DQ0"] = False
                        self.digital_outputs["DQ1"] = False
                        self.digital_outputs["DQ2"] = False
                        self.digital_outputs["DQ3"] = False
                    elif self.alarms["A2"]["Active"]:
                        self.digital_outputs["DQ2"] = False
                        self.digital_outputs["DQ3"] = True

                    elif self.alarms["A3"]["Active"]:
                        self.digital_outputs["DQ2"] = False
                        self.digital_outputs["DQ3"] = True

                    elif self.alarms["A4"]["Active"]:
                        self.digital_outputs["DQ0"] = False
                        self.digital_outputs["DQ1"] = False
                        self.digital_outputs["DQ2"] = False
                        self.digital_outputs["DQ3"] = False

                    elif self.alarms["A5"]["Active"]:
                        self.digital_outputs["DQ0"] = False
                        self.digital_outputs["DQ1"] = False
                        self.digital_outputs["DQ2"] = False
                        self.digital_outputs["DQ3"] = True

                    else:
                        self.digital_outputs["DQ0"] = False
                        self.digital_outputs["DQ1"] = False
                        self.digital_outputs["DQ2"] = False
                        self.digital_outputs["DQ3"] = False

                # Implement output logic:
                #   This should set the digital outputs based on the current step and alarm conditions.
                #   For example, the output is True when step is "Start" and no alarm is active.
                self.digital_outputs["DQ0"] = False
                self.digital_outputs["DQ1"] = False
                self.digital_outputs["DQ2"] = False
                self.digital_outputs["DQ3"] = False

                if self.step == PLCStep.STOP:
                    pass
                elif self.step == PLCStep.PREFILL and not self.prefill_ready:
                    self.digital_outputs["DQ0"] = True
                elif self.step == PLCStep.FILL:
                    self.digital_outputs["DQ0"] = True
                elif self.step == PLCStep.HEAT:
                    self.digital_outputs["DQ2"] = True
                elif self.step == PLCStep.DISCHARGE:
                    self.digital_outputs["DQ1"] = True
                elif self.step == PLCStep.ERROR:
                    self.digital_outputs["DQ3"] = True

                await self.set_alarms()

                # Setting outputs on server
                await self.write_outputs()
                # Sleeping for cycle time
                await asyncio.sleep(self.cycle_time)
        finally:
            await self.server.stop()
            print("Stopping server")

    async def set_opcua_server(self):
        self.server = Server()
        await self.server.init()
        self.server.set_endpoint(
            f"opc.tcp://localhost:{self.port}/freeopcua/server/"
        )

        # set up our own namespace, not really necessary but should as spec
        uri = "http://examples.freeopcua.github.io"
        self.idx = await self.server.register_namespace(uri)

        # get Objects node, this is where we should put our nodes
        objects = self.server.get_objects_node()

        # populating our address space
        self.myobj = await objects.add_object(self.idx, "myPLC")

        for key, value in self.digital_inputs.items():
            myvar = await self.myobj.add_variable(self.idx, key, value)
            await myvar.set_writable()
        for key, value in self.analog_inputs.items():
            myvar = await self.myobj.add_variable(self.idx, key, value)
            await myvar.set_writable()
        for key, value in self.digital_outputs.items():
            myvar = await self.myobj.add_variable(self.idx, key, value)
            await myvar.set_writable()
        for key, values in self.alarms.items():
            myalarm = await self.myobj.add_object(self.idx, key)
            for newkey, value in values.items():
                myvar = await myalarm.add_variable(self.idx, newkey, value)
                await myvar.set_writable()

        # starting!
        await self.server.start()
        print("Server started")

    async def stop(self):
        await self.server.stop()

    async def main(self):
        # Set OPC UA server
        await self.set_opcua_server()

        # Execute cycle program
        await self.execute_control_logic()


if __name__ == "__main__":

    # simulate = (os.environ.get("SIMULATE_START", "false").lower() == "true")
    plc = PLCSimulator(port=int(os.environ.get("OPCUA_PORT", 4840)),
                       auto_update_inputs=True,
                       simulate_start=True)
    try:
        asyncio.run(plc.main())
    except KeyboardInterrupt:
        print("PLC stopped")
