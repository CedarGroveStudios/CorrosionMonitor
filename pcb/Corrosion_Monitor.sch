EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr USLetter 11000 8500
encoding utf-8
Sheet 1 1
Title "Corrosion_Monitor"
Date "2021-03-04"
Rev "v00"
Comp "Cedar Grove Studios"
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L power:+3V3 #PWR0119
U 1 1 5F9CCF22
P 5800 2625
F 0 "#PWR0119" H 5800 2475 50  0001 C CNN
F 1 "+3V3" H 5815 2798 50  0000 C CNN
F 2 "" H 5800 2625 50  0001 C CNN
F 3 "" H 5800 2625 50  0001 C CNN
	1    5800 2625
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR0122
U 1 1 5F9D79E7
P 5400 4125
F 0 "#PWR0122" H 5400 3875 50  0001 C CNN
F 1 "GND" H 5405 3952 50  0000 C CNN
F 2 "" H 5400 4125 50  0001 C CNN
F 3 "" H 5400 4125 50  0001 C CNN
	1    5400 4125
	1    0    0    -1  
$EndComp
$Comp
L dk_Transistors-FETs-MOSFETs-Single:2N7000 Q1
U 1 1 6041F6F4
P 5800 3525
F 0 "Q1" H 5908 3578 60  0000 L CNN
F 1 "TN0104" H 5908 3472 60  0000 L CNN
F 2 "Package_TO_SOT_THT:TO-92S" H 6000 3725 60  0001 L CNN
F 3 "https://www.onsemi.com/pub/Collateral/NDS7002A-D.PDF" H 6000 3825 60  0001 L CNN
F 4 "2N7000FS-ND" H 6000 3925 60  0001 L CNN "Digi-Key_PN"
F 5 "2N7000" H 6000 4025 60  0001 L CNN "MPN"
F 6 "Discrete Semiconductor Products" H 6000 4125 60  0001 L CNN "Category"
F 7 "Transistors - FETs, MOSFETs - Single" H 6000 4225 60  0001 L CNN "Family"
F 8 "https://www.onsemi.com/pub/Collateral/NDS7002A-D.PDF" H 6000 4325 60  0001 L CNN "DK_Datasheet_Link"
F 9 "/product-detail/en/on-semiconductor/2N7000/2N7000FS-ND/244278" H 6000 4425 60  0001 L CNN "DK_Detail_Page"
F 10 "MOSFET N-CH 60V 200MA TO-92" H 6000 4525 60  0001 L CNN "Description"
F 11 "ON Semiconductor" H 6000 4625 60  0001 L CNN "Manufacturer"
F 12 "Active" H 6000 4725 60  0001 L CNN "Status"
	1    5800 3525
	1    0    0    -1  
$EndComp
$Comp
L Motor:Fan M1
U 1 1 60421DBB
P 5800 3025
F 0 "M1" H 5958 3121 50  0000 L CNN
F 1 "Fan" H 5958 3030 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" H 5800 3035 50  0001 C CNN
F 3 "~" H 5800 3035 50  0001 C CNN
	1    5800 3025
	1    0    0    -1  
$EndComp
$Comp
L Device:R_Small R1
U 1 1 604235FB
P 5400 3825
F 0 "R1" H 5459 3871 50  0000 L CNN
F 1 "100k" H 5459 3780 50  0000 L CNN
F 2 "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical" H 5400 3825 50  0001 C CNN
F 3 "~" H 5400 3825 50  0001 C CNN
	1    5400 3825
	1    0    0    -1  
$EndComp
$Comp
L Device:D D1
U 1 1 60423CEB
P 6200 2975
F 0 "D1" V 6154 3055 50  0000 L CNN
F 1 "D" V 6245 3055 50  0000 L CNN
F 2 "Diode_THT:D_T-1_P2.54mm_Vertical_KathodeUp" H 6200 2975 50  0001 C CNN
F 3 "~" H 6200 2975 50  0001 C CNN
	1    6200 2975
	0    1    1    0   
$EndComp
$Comp
L Connector:Conn_01x03_Female J1
U 1 1 604249C6
P 4925 3725
F 0 "J1" H 5275 4025 50  0000 C CNN
F 1 "Stemma 3-pin" H 5050 3950 50  0000 C CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical" H 4925 3725 50  0001 C CNN
F 3 "~" H 4925 3725 50  0001 C CNN
	1    4925 3725
	-1   0    0    -1  
$EndComp
Wire Wire Line
	5800 2675 6200 2675
Wire Wire Line
	6200 2675 6200 2825
Wire Wire Line
	6200 3125 6200 3275
Wire Wire Line
	6200 3275 5800 3275
Wire Wire Line
	5800 3275 5800 3225
Wire Wire Line
	5800 2725 5800 2675
Wire Wire Line
	5800 2675 5800 2625
Connection ~ 5800 2675
Wire Wire Line
	5800 3275 5800 3325
Connection ~ 5800 3275
Wire Wire Line
	5500 3625 5400 3625
Wire Wire Line
	5400 3625 5400 3725
Wire Wire Line
	5400 3925 5400 4025
Wire Wire Line
	5800 4025 5800 3725
Wire Wire Line
	5400 4125 5400 4025
Wire Wire Line
	5400 3625 5125 3625
Connection ~ 5400 3625
Wire Wire Line
	5275 3725 5275 2675
Wire Wire Line
	5275 2675 5800 2675
Wire Wire Line
	5125 3725 5275 3725
Wire Wire Line
	5125 3825 5275 3825
Wire Wire Line
	5275 3825 5275 4025
Wire Wire Line
	5275 4025 5400 4025
Connection ~ 5400 4025
Wire Wire Line
	5400 4025 5800 4025
$EndSCHEMATC
