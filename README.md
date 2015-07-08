# Virtual WiFi cells (vwc)

The purpose of Python scripts in this project is to read a Hunter scan log file and group APs into virtual WiFi cells. The scripts output JSON compatible file containing virtual WiFi cells.

## Version 1

**Cell condition (cc):**
Defines the minimum factor *cc* of overlap to include the next scan into an intermediate cell. When a scan is encountered for which the cell condition is no longer valid, the intermediate cell is finalised and a new intermediate cell is created. The process repeats until there are no more scans.

*Note:*
- The overlap is defined as common APs between an intermediate cell and the next scan.
- An intermediate cell is just a group of scans sharing a minimum factor of overlap.

**Overlap condition (oc):**
The overlap condition checks for the overlap in APs between any two virtual cells and gets the GPS coordinate which records an overlap defined by the *oc* factor range. This process is repeated for every cell against every other cell. However, in the code the process can be restricted to immediate neighbours or neighbour of neighbour, etc.

## Version 2 (in progress)

**Cell condition:**
Will be the same as above.

**Overlap condition:**
The overlap condition will check for overlap in APs between adjacent or neighbour of neighbour scans. Note the difference from above is that we are checking for overlap between scans and not between cells. Also note that the overlap will be defined by the *oc* factor and not the factor range.

