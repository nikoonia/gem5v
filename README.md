# gem5v

A Modified gem5 for Simulating Virtualized Systems

## Introduction
"The [gem5] simulator is a modular platform for computer system architecture research, encompassing system-level architecture as well as processor microarchitecture".
Gem5v is a modified version of gem5 that simulates the behavior of a virtualization layer and can simulate virtual machines.
Gem5v is developed in [DSD Lab], [School of ECE], [University of Tehran] and is presented in a Supercomputing Journal article:

Seyed Hossein Nikounia and Siamak Mohammadi, "[Gem5v: a modified gem5 for simulating virtualized systems]", The Journal of Supercomputing, 2015, DOI: 10.1007/s11227-014-1375-7.

## How to Make

The build procedure is the same as the original gem5. 
Please consult [gem5's documentation] for more.

## How to Use

An script called hypervisor.py is added to configs/example.
You may use it like other gem5's configuration scripts.
Description of the arguments are given in "hypervisor.py -h".

## Contact

If you have any question about this project, please don't hesitate to contact me: nikoonia at sign ut dot ac dot ir

[gem5's documentation]: http://www.gem5.org/Documentation

[gem5]: http://gem5.org

[University of Tehran]: http://ut.ac.ir/en

[School of ECE]: http://ece.ut.ac.ir

[DSD Lab]: http://ece.ut.ac.ir/dsdlab/Home.html

[Gem5v: a modified gem5 for simulating virtualized systems]: http://link.springer.com/article/10.1007%2Fs11227-014-1375-7
