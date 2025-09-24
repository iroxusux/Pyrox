
# Checklist Template

## Designer: Trevor Hurley

### Integrator: Brian LaFond

#### Indicon LLC

##### Power Distribution Panel  

Shut Off The **PDP Panel Disconnect.**  
Verify That **xxxPDPxSfty.M.DiscOn** Is Not Active.

Shut Off The **PDP Panel Disconnect.**  
Verify That **Manual Intervention Message** Appears.  
"*xxxPDPx Control Power Distribution Panel Disconnect Not On. Col#*"

Remove Power From The **Surge Protection Device.**  
Verify That **Manual Intervention Message** Appears.  
"*xxxPDPx Surge Protection Disconnect Off. Col#*"

Remove Power From **QA01 Circuit Breaker.**  
Verify That **Fault Message** Of First Device Appears.  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **QA02 Circuit Breaker.**  
Verify That **Fault Message** Of First Device Appears.  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **QA03 Circuit Breaker.**  
Verify That **Fault Message** Of First Device Appears.  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **QA04 Circuit Breaker.**  
Verify That **Fault Message** Of First Device Appears.  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **QA05 Circuit Breaker.**  
Verify That **Fault Message** Of First Device Appears.  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **QA06 Circuit Breaker.**  
Verify That **Fault Message** Of First Device Appears.  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **QA07 Circuit Breaker.**  
Verify That **Fault Message** Of First Device Appears.  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **QA08 Circuit Breaker.**  
Verify That **Fault Message** Of First Device Appears.  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **QA09 Circuit Breaker.**  
Verify That **Fault Message** Of First Device Appears.  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **QA10 Circuit Breaker.**  
Verify That **Fault Message** Of First Device Appears.  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **1AC01 Circuit Breaker.**  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **1AC02 Circuit Breaker.**  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **1AC03 Circuit Breaker.**  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **1AC04 Circuit Breaker.**  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **1AC05 Circuit Breaker.**  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **1AC06 Circuit Breaker.**  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **1AC07 Circuit Breaker.**  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **1AC08 Circuit Breaker.**  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **1AC09 Circuit Breaker.**  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **1AC10 Circuit Breaker.**  
"*xxxxxxx Communication Faulted Col.#*"  
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

##### HMI  

Verify **Device IP** Is Correct, And That The **Safety Network Number** Is Unique To This Device.  

Verify That The **Requested Packet Interval (RPI)** Is Set To **20ms**  

**Remove Communications** To The HMI Enclosure.  
Verify That **Fault Message** Appears.  
"*HMIx Enclosure Safety IO Comm Fault Col.#*"  
Verify That No Other Alarms Appear.

**Remove Communications** To The HMI PanelView.  
Verify That **Fault Message** Appears.  
"*HMIx PV Communication Heartbeat Lost Col.#*"  
Verify That No Other Alarms Appear.  

Verify Correct **Input Configuration** In The Devices Properties Pane.  

Verify Correct **Test Output Configuration** In The Devices Properties Pane.  

Press In HMI Panel **E-Stop PushButton.** 
Verify That **Manual Intervention Message** Appears.  
"*HMIx Panel E-Stop PB Pressed Col.#*"  
Verify That The Red Mushroom Pushbutton Is Illuminated.  
Verify That All Station Within Span Of Control Are Stopped.

Pull Out The HMI Panel **E-Stop PushButton.**  
Without Resetting, Verify That **Manual Intervention Message** Appears.  
"*HMIx Panel E-Stop Not Reset Col.#*"

Verify That The **E-Stop Reset PushButton Is Flashing** When Ready For Reset.

Verify That The **E-Stop Reset PushButton** Resets All E-Stops Within Span Of Control.  
Verify The PushButton Is Illuminated When E-Stops Are Reset.

Verify That The **Selector Switch** Sets All Stations Within It's Span Of Control To Auto Mode.

Verify That The **Selector Switch** Sets All Stations Within It's Span Of Control To Manual Mode.  
Verify That **Manual Intervention Message** Appears.  
"*HMIx Panel Manual Mode Selected Col.#*"  

Verify That The **Selector Switch** Sets All Stations Within It's Span Of Control To No Mode.  

Verify That The **Auto Initiate PushButton** Is Flashing When All Stations Are Ready For Auto.  

Verify That The **Auto Initiate PushButton** Starts Up All Stations Within It's Span Of Control.  
Verify That The PushButton Is Illuminated When All Stations Are In Auto.  

##### Safety I/O Block  
 
Verify **Device IP** Is Correct, And That The **Safety Network Number** Is Unique To This Device.  

Verify That The **Requested Packet Interval (RPI)** Is Set To **20ms**  

**Remove Communications** To This Device.  
Verify That **Fault Message** Appears.  
"*xxxSBKx Communications Faulted Col.#*"  
Verify That No Other Alarms Appear.  

Flag All Connected Devices To Verify **Input Mapping** Is Correct.  

Verify Correct **Safety Mapping Outputs.**  
*i.e. xxxSBKx.M.SafetyOut0*  

Verify Correct **Input Configuration** In The Devices Properties Pane.  

Verify Correct **Test Output Configuration** In The Devices Properties Pane.  

##### I/O Block  

Verify **Device IP** Is Correct.  

**Remove Communications** To This Device.  
Verify That **Fault Message** Appears.  
"*xxxBLKx Communications Faulted Col.#*"  
Verify That No Other Alarms Appear.  

Flag All Connected Devices To Verify **Input Mapping** Is Correct.  

If Device Uses **Aux Power** From Another Device, Verify That The **CommEdit** Mapping Is Properly Configured.  
*i.e. xxxBLKx.M.UsesAuxPwr*  

##### Production Spacing Conveyor  

Verify **Main VFD IP** Is Correct, And That The **Safety Network Number** Is Unique To This Device.  

Verify That The **Requested Packet Interval (RPI)** Of The **Main VFD** Is Set To **20ms**  

**Remove Communications** To The **Main VFD*.  
Verify That **Fault Message** Appears.  
"*xxxVFDx Communications Faulted Col.#*"  
Verify That No Other Alarms Appear.  

Flag All Connected Devices To Verify **Input Mapping** Is Correct.  

Shut Off The **Main VFD Drive Disconnect**.  
Verify That **Manual Intervention Message** Appears.  
"*xxxVFDx Drive Disconnect Off Col.#*"  

Verify **xxx.M.MainAirOk** Is Mapped To The Correct Input.  
Force Input Off, And Verify **Fault Message** Appears.  
"*xxx Spacer Air Pressure Fault Col.#*"

With The Corresponding HMI In **Manual Mode**, Verify **Forward Jogging Motion.** 

With The Corresponding HMI In **Manual Mode**, Verify **Index In Motion.**  
Current And Previous Conveyor Should Jog Forward.  

With The Corresponding HMI In **Manual Mode**, Verify **Index Out Motion.**  
Current And Next Conveyor Should Jog Forward.

With The Corresponding HMI In **Manual Mode**, Verify **Extending Motion** Of The **Skid Spacer Shot Pins.**  

With The Corresponding HMI In **Manual Mode**, Verify **Retracting Motion** Of The **Skid Spacer Shot Pins.**  

With The Corresponding HMI In **Manual Mode**, Verify The **Sequence Of Operations.**  

With The Corresponding HMI In **Auto Mode**, **Hold** The Current Conveyor.  
Verify That **Manual Intervention Message** Appears.  
"*xxx In Station Pallet/Skid Hold Col.#*"  

With The **Conveyor Running In Auto**, Trip The **OverTorque Limit Switch.**  
Verify That The Conveyor Motion Stops.  
Verify That **Fault Message** Appears.  
"*xxx Chain Conveyor Over Torque Fault. Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Entering Switch** To Remain **Off**, So That It Is Not Made.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Entering Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Entering Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Entering Switch Still On Fault Col.#*"  

Similar To Previous, With The **Conveyor Running In Auto**, Index In A Skid. Force The **Entering Switch** To Remain **On** As Well As The **xxx.M.PrevExiting Bit**.  
Verify **Fault Message** Appears.  
"*xxx Index In Over Time Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **In Position Switch** To Remain **Off**, So That It Is Not Made.  
Verify That **Fault Message** Appears.  
"*xxx Pallet/Skid In Position Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **In Position Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid In Position Switch Still On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Spacing Clear Setup Switch** To Remain **Off**, So That It Is Not Made.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Spacing Clear Setup Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Spacing Clear Setup Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Spacing Clear Setup Switch Still On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Part Present Switch** To Remain **Off**, So That It Is Not Made.  
Verify **Fault Message** Appears.  
"*xxx Part Present Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Part Present Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Part Present Switch Still On Fault Col.#*"  

Extend The **Spacer Shot Pins**. Force The **Extended Switch** To Remain **Off**.  
Verify **Fault Message** Appears.  
"*xxx Skid Spacer Shot Pins Extended Switch Not On Fault Col.#*"  

Retract The **Spacer Shot Pins**. Force The **Extended Switch** To Remain **On**.  
Verify **Fault Message** Appears.  
"*xxx Skid Spacer Shot Pins Extended Switch Still On Fault Col.#*"  

Retract The **Spacer Shot Pins**. Force The **Retracted Switch** To Remain **Off**.  
Verify **Fault Message** Appears.  
"*xxx Skid Spacer Shot Pins Retracted Switch Not On Fault Col.#*"  

Extend The **Spacer Shot Pins**. Force The **Retracted Switch** To Remain **Off**.  
Verify **Fault Message** Appears.  
"*xxx Skid Spacer Shot Pins Retracted Switch Still On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index Out A Skid. With The Station Clear To Exit, Force The **Exiting Switch** To Remain **Off**, So That It Is Not Made.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Exiting Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index Out A Skid. Force The **Exiting Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Exiting Switch Still On Fault Col.#*"  

##### RunStop  

Verify **RunStop Inputs** Are Correctly Mapped.  

Press The **RunStop PushButton**.  
Verify That All Stations Within It's Span Of Control Are Stopped.  
Verify **Manual Intervention Message** Appears.  
"*xxx Run Stop Pressed At Col.#*"  

**Force On** (Or Off) **Both RunStop Inputs**.  
Verify That All Stations Within It's Span Of Control Are Stopped.  
After 5 Second, Verify That **Fault Message** Appears.  
"*xxx Run Stop PB #xx Validation Fault Col.#*"  

##### Production Conveyor  

Verify **Main VFD IP** Is Correct, And That The **Safety Network Number** Is Unique To This Device.  

Verify That The **Requested Packet Interval (RPI)** Of The **Main VFD** Is Set To **20ms**  

**Remove Communications** To The **Main VFD**.  
Verify That **Fault Message** Appears.  
"*xxxVFDx Communications Faulted Col.#*"  
Verify That No Other Alarms Appear.  

Flag All Connected Devices To Verify **Input Mapping** Is Correct.  

Shut Off The **Main VFD Drive Disconnect**.  
Verify That **Manual Intervention Message** Appears.  
"*xxxVFDx Drive Disconnect Off Col.#*"  

With The Corresponding HMI In **Manual Mode**, Verify **Forward Jogging Motion.** 

With The Corresponding HMI In **Manual Mode**, Verify **Index In Motion.**  
Current And Previous Conveyor Should Jog Forward.  

With The Corresponding HMI In **Manual Mode**, Verify **Index Out Motion.**  
Current And Next Conveyor Should Jog Forward.

With The Corresponding HMI In **Manual Mode**, Verify The **Sequence Of Operations.**  

With The Corresponding HMI In **Auto Mode**, **Hold** The Current Conveyor.  
Verify That **Manual Intervention Message** Appears.  
"*xxx In Station Pallet/Skid Hold Col.#*"  

With The **Conveyor Running In Auto**, Trip The **OverTorque Limit Switch.**  
Verify That The Conveyor Motion Stops.  
Verify That **Fault Message** Appears.  
"*xxx Chain Conveyor Over Torque Fault. Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Entering Switch** To Remain **Off**, So That It Is Not Made.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Entering Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Entering Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Entering Switch Still On Fault Col.#*"  

Similar To Previous, With The **Conveyor Running In Auto**, Index In A Skid. Force The **Entering Switch** To Remain **On** As Well As The **xxx.M.PrevExiting Bit**.  
Verify **Fault Message** Appears.  
"*xxx Index In Over Time Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **In Position Switch** To Remain **Off**, So That It Is Not Made.  
Verify That **Fault Message** Appears.  
"*xxx Pallet/Skid In Position Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **In Position Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid In Position Switch Still On Fault Col.#*"     

With The **Conveyor Running In Auto**, Index Out A Skid. With The Station Clear To Exit, Force The **Exiting Switch** To Remain **Off**, So That It Is Not Made.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Exiting Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index Out A Skid. Force The **Exiting Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Exiting Switch Still On Fault Col.#*"  

##### Power Roll Bed  

Verify **Main VFD IP** Is Correct, And That The **Safety Network Number** Is Unique To This Device.  

Verify That The **Requested Packet Interval (RPI)** Of The **Main VFD** Is Set To **20ms**  

**Remove Communications** To The **Main VFD**.  
Verify That **Fault Message** Appears.  
"*xxxVFDx Communications Faulted Col.#*"  
Verify That No Other Alarms Appear.  

Flag All Connected Devices To Verify **Input Mapping** Is Correct.  

Shut Off The **Main VFD Drive Disconnect**.  
Verify That **Manual Intervention Message** Appears.  
"*xxxVFDx Drive Disconnect Off Col.#*"  

With The Corresponding HMI In **Manual Mode**, Verify **Forward Jogging Motion.** 

With The Corresponding HMI In **Manual Mode**, Verify **Index In Motion.**  
Current And Previous Conveyor Should Jog Forward.  

With The Corresponding HMI In **Manual Mode**, Verify **Index Out Motion.**  
Current And Next Conveyor Should Jog Forward.

With The Corresponding HMI In **Manual Mode**, Verify The **Sequence Of Operations.**  

With The Corresponding HMI In **Auto Mode**, **Hold** The Current Conveyor.  
Verify That **Manual Intervention Message** Appears.  
"*xxx In Station Pallet/Skid Hold Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Entering Switch** To Remain **Off**, So That It Is Not Made.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Entering Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Entering Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Entering Switch Still On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **In Position Switch** To Remain **Off**, So That It Is Not Made.  
Verify That **Fault Message** Appears.  
"*xxx Pallet/Skid In Position Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **In Position Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid In Position Switch Still On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Decel Switch** To Remain **Off**, So That It Is Not Made.  
Verify That **Fault Message** Appears.  
"*xxx Pallet/Skid Decel Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index Out A Skid. Force The **Decel Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Decel Switch Still On Fault Col.#*"

With The **Conveyor Running In Auto**, Index Out A Skid. With The Station Clear To Exit, Force The **Exiting Switch** To Remain **Off**, So That It Is Not Made.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Exiting Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index Out A Skid. Force The **Exiting Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Exiting Switch Still On Fault Col.#*"  

##### Lift Table

Verify **Power Roll Bed VFD IP** Is Correct, And That The **Safety Network Number** Is Unique To This Device.  

Verify That The **Requested Packet Interval (RPI)** Of The **Power Roll Bed VFD** Is Set To **20ms**  

**Remove Communications** To The **Power Roll Bed VFD**.  
Verify That **Fault Message** Appears.  
"*xxxVFDx Communications Faulted Col.#*"  
Verify That No Other Alarms Appear.  

Flag All Connected Devices To Verify **Input Mapping** Is Correct.  

Verify **Lift Table VFD IP** Is Correct, And That The **Safety Network Number** Is Unique To This Device.  

Verify That The **Requested Packet Interval (RPI)** Of The **Lift Table VFD** Is Set To **20ms**  

**Remove Communications** To The **Lift Table VFD**.  
Verify That **Fault Message** Appears.  
"*xxxVFDx Communications Faulted Col.#*"  
Verify That No Other Alarms Appear.  

Flag All Connected Devices To Verify **Input Mapping** Is Correct.  

Shut Off The **Lift Table VFD Drive Disconnect**.  
Verify That **Manual Intervention Message** Appears.  
"*xxxVFDx Drive Disconnect Off Col.#*"  

With The Corresponding HMI In **Manual Mode**, Verify **PRB Forward Jogging Motion.** 

With The Corresponding HMI In **Manual Mode**, Verify **PRB Index In Motion.**  
Current And Previous Conveyor Should Jog Forward.  

With The Corresponding HMI In **Manual Mode**, Verify **PRB Index Out Motion.**  
Current And Next Conveyor Should Jog Forward.

With The Corresponding HMI In **Manual Mode**, Verify The **PRB Sequence Of Operations.**  

With The Corresponding HMI In **Manual Mode**, Verify The **LT Raise Jogging Motion**  

With The Corresponding HMI In **Manual Mode**, Verify The **LT Lower Jogging Motion**  

With The Corresponding HMI In **Manual Mode**, Verify The **LT Sequence Of Operations.**  

With The Corresponding HMI In **Auto Mode**, **Hold** The Current Conveyor.  
Verify That **Manual Intervention Message** Appears.  
"*xxx In Station Pallet/Skid Hold Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Entering Switch** To Remain **Off**, So That It Is Not Made.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Entering Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Entering Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Entering Switch Still On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **In Position Switch** To Remain **Off**, So That It Is Not Made.  
Verify That **Fault Message** Appears.  
"*xxx Pallet/Skid In Position Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **In Position Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid In Position Switch Still On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index In A Skid. Force The **Decel Switch** To Remain **Off**, So That It Is Not Made.  
Verify That **Fault Message** Appears.  
"*xxx Pallet/Skid Decel Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index Out A Skid. Force The **Decel Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Decel Switch Still On Fault Col.#*"

With The **Conveyor Running In Auto**, Index Out A Skid. With The Station Clear To Exit, Force The **Exiting Switch** To Remain **Off**, So That It Is Not Made.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Exiting Switch Not On Fault Col.#*"  

With The **Conveyor Running In Auto**, Index Out A Skid. Force The **Exiting Switch** To Remain **On** After The Skid Exits.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Exiting Switch Still On Fault Col.#*"

With The **Conveyor Running In Auto**, Index A Skid Onto The Lift Table. Force The **In Position A Over Lift Table Switch** To Remain **Off**.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Over Lift Table Position A Switch Not On Fault Col.#*"

With The **Conveyor Running In Auto**, Index Out A Skid From The Lift Table. Force The **In Position A Over Lift Table Switch** To Remain **On**.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Over Lift Table Position A Switch Still On Fault Col.#*"

With The **Conveyor Running In Auto**, Index A Skid Onto The Lift Table. Force The **In Position B Over Lift Table Switch** To Remain **Off**.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Over Lift Table Position B Switch Not On Fault Col.#*"

With The **Conveyor Running In Auto**, Index Out A Skid From The Lift Table. Force The **In Position B Over Lift Table Switch** To Remain **On**.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Over Lift Table Position B Switch Still On Fault Col.#*"

With The Conveyor **Conveyor Running In Auto**, **Remove Lock Pin #1**.  
Verify That Lock Pin Removal Inhibits Motion To Table.  
Verify That **Manual Intervention Message** Appears.  
"*xxx MPSx Lock Pin Not In Storage Col.#*"  

With The Conveyor **Conveyor Running In Auto**, **Remove Lock Pin #2**.  
Verify That Lock Pin Removal Inhibits Motion To Table.  
Verify That **Manual Intervention Message** Appears.  
"*xxx MPSx Lock Pin Not In Storage Col.#*"  

With The Conveyor **Conveyor Running In Auto**, **Remove Lock Pin #3**.  
Verify That Lock Pin Removal Inhibits Motion To Table.  
Verify That **Manual Intervention Message** Appears.  
"*xxx MPSx Lock Pin Not In Storage Col.#*"  

With The Conveyor **Conveyor Running In Auto**, **Remove Lock Pin #4**.  
Verify That Lock Pin Removal Inhibits Motion To Table.  
Verify That **Manual Intervention Message** Appears.  
"*xxx MPSx Lock Pin Not In Storage Col.#*"  

##### Hold Table

Flag All Connected Devices To Verify **Input Mapping** Is Correct.  

Verify **Lift Table VFD IP** Is Correct, And That The **Safety Network Number** Is Unique To This Device.  

Verify That The **Requested Packet Interval (RPI)** Of The **Lift Table VFD** Is Set To **20ms**  

**Remove Communications** To The **Lift Table VFD**.  
Verify That **Fault Message** Appears.  
"*xxxVFDx Communications Faulted Col.#*"  
Verify That No Other Alarms Appear.  

Flag All Connected Devices To Verify **Input Mapping** Is Correct.  

Shut Off The **Lift Table VFD Drive Disconnect**.  
Verify That **Manual Intervention Message** Appears.  
"*xxxVFDx Drive Disconnect Off Col.#*"  

Verify **xxx.M.MainAirOk** Is Mapped To The Correct Input.  
Force Input Off, And Verify **Fault Message** Appears.  
"*xxx Air Pressure Fault Col.#*"

With The Corresponding HMI In **Manual Mode**, Verify The **LT Raise Jogging Motion**  

With The Corresponding HMI In **Manual Mode**, Verify The **LT Lower Jogging Motion**   

With The Corresponding HMI In **Manual Mode**, Verify The **LT Pin Stop Raise Motion**  

With The Corresponding HMI In **Manual Mode**, Verify The **LT Pin Stop Lower Motion**  

With The Corresponding HMI In **Manual Mode**, Verify The **LT Sequence Of Operations.** 

With The Corresponding HMI In **Auto Mode**, **Hold** The Current Conveyor.  
Verify That **Manual Intervention Message** Appears.  
"*xxx In Station Pallet/Skid Hold Col.#*"  

With The **Conveyor Running In Auto**, Index A Skid Onto The Lift Table. Force The **In Position A Over Lift Table Switch** To Remain **Off**.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Over Lift Table Position A Switch Not On Fault Col.#*"

With The **Conveyor Running In Auto**, Index Out A Skid From The Lift Table. Force The **In Position A Over Lift Table Switch** To Remain **On**.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Over Lift Table Position A Switch Still On Fault Col.#*"

With The **Conveyor Running In Auto**, Index A Skid Onto The Lift Table. Force The **In Position B Over Lift Table Switch** To Remain **Off**.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Over Lift Table Position B Switch Not On Fault Col.#*"

With The **Conveyor Running In Auto**, Index Out A Skid From The Lift Table. Force The **In Position B Over Lift Table Switch** To Remain **On**.  
Verify **Fault Message** Appears.  
"*xxx Pallet/Skid Over Lift Table Position B Switch Still On Fault Col.#*"

Extend The **Lift Table Pin Stops**. Force The **Pin Stop A Raised Switch** To Remain **Off**.  
Verify **Fault Message** Appears.  
"*xxx Pin Stop A Raised Switch Not On Fault Col.#*"  

Retract The **Lift Table Pin Stops**. Force The **Pin Stop A Raised Switch** To Remain **On**.  
Verify **Fault Message** Appears.  
"*xxx Pin Stop A Raised Switch Still On Fault Col.#*"  

Extend The **Lift Table Pin Stops**. Force The **Pin Stop B Raised Switch** To Remain **Off**.  
Verify **Fault Message** Appears.  
"*xxx Pin Stop B Raised Switch Not On Fault Col.#*"  

Retract The **Lift Table Pin Stops**. Force The **Pin Stop B Raised Switch** To Remain **On**.  
Verify **Fault Message** Appears.  
"*xxx Pin Stop B Raised Switch Still On Fault Col.#*"  

With The Conveyor **Conveyor Running In Auto**, **Remove Lock Pin #1**.  
Verify That Lock Pin Removal Inhibits Motion To Table.  
Verify That **Manual Intervention Message** Appears.  
"*xxx MPSx Lock Pin Not In Storage Col.#*"  

With The Conveyor **Conveyor Running In Auto**, **Remove Lock Pin #2**.  
Verify That Lock Pin Removal Inhibits Motion To Table.  
Verify That **Manual Intervention Message** Appears.  
"*xxx MPSx Lock Pin Not In Storage Col.#*"  

With The Conveyor **Conveyor Running In Auto**, **Remove Lock Pin #3**.  
Verify That Lock Pin Removal Inhibits Motion To Table.  
Verify That **Manual Intervention Message** Appears.  
"*xxx MPSx Lock Pin Not In Storage Col.#*"  

With The Conveyor **Conveyor Running In Auto**, **Remove Lock Pin #4**.  
Verify That Lock Pin Removal Inhibits Motion To Table.  
Verify That **Manual Intervention Message** Appears.  
"*xxx MPSx Lock Pin Not In Storage Col.#*"  

##### Cross Transfer

Verify **Main VFD IP** Is Correct, And That The **Safety Network Number** Is Unique To This Device.  

Verify That The **Requested Packet Interval (RPI)** Of The **Main VFD** Is Set To **20ms**  

**Remove Communications** To The **Main VFD*.  
Verify That **Fault Message** Appears.  
"*xxxVFDx Communications Faulted Col.#*"  
Verify That No Other Alarms Appear.  

Flag All Connected Devices To Verify **Input Mapping** Is Correct.  

Shut Off The **Main VFD Drive Disconnect**.  
Verify That **Manual Intervention Message** Appears.  
"*xxxVFDx Drive Disconnect Off Col.#*"  

With The Corresponding HMI In **Manual Mode**, Verify **Forward Jogging Motion.**  

With The Corresponding HMI In **Manual Mode**, Verify **Reverse Jogging Motion.**  

With The Corresponding HMI In **Manual Mode**, Verify The **Sequence Of Operations.**  

With The Corresponding HMI In **Auto Mode**, **Hold** The Current Conveyor.  
Verify That **Manual Intervention Message** Appears.  
"*xxx In Station Pallet/Skid Hold Col.#*"  

With The **Conveyor Running In Auto**, Trip The **OverTorque Limit Switch.**  
Verify That The Conveyor Motion Stops.  
Verify That **Fault Message** Appears.  
"*xxx Cross Transfer Over Torque Fault. Col.#*"  

##### End Of Travel

Verify That The **EOTInstalled.XX** Bit Is Set To **OTE** If Installed, Or **OTU** If Not Installed.  

Verify **EOTLS1 & EOTLS2 Inputs** Are Properly Mapped.  

Trip **EOTLS1**.  
Verify **Warning Message** Appears.  
"*xxx EOTLS1 End Of Travel Warning Col.#*"  

Trip **EOTLS1**.  
Verify Corresponding **Stack Light** Is Flashing.  

Trip **EOTLS2**.  
Verify **Fault Message** Appears.  
"*xxx EOTLS2 End Of Travel Faulted Col.#*"  
Verify Corresponding Stations Are Stopped.  

Trip **EOTLS2**.  
Verify Corresponding **Stack Light** Is On, And Horn Is On.
