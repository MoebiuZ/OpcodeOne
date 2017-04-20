OpcodeOne (O¹) Project
======================

Educational exploration on several aspects of computing through the design and implementation of a fictional CPU architecture.



## Purpose


The only purpose of this project is self learning / knowledge sharing via experimentation.

Based on my experience, working on "toy projects" without a real world application like this are a great tool for exercising your skills, to learn a wide range of new topics and to understand better how more complex systems work. And of course, to have a lot of fun.

While writting your own architecture would seem like a waste of time (*Why would I learn a fake architecture while I could learn x86?*), I can ensure you this kind of exercises lay the foundations to better understand how computers work, and is a great playground to improve skills like reverse engineering and programming. I you love retro computers you will understand what I mean.

This repository is also a "self-learning framework" that I hope will serve in the future as a *guide* to develop courses or master classes from a self-learning perspective to complement more formal education (that nowadays is somehow *lacking* and biased for a healthy self-development).

During this journey several topics will be exercised, and is great to learn or improve things like:

* General CPU internals
* Low level programming
* Simulation / Emulation
* C++ programming
* Python programming
* ARM assembly
* Lisp, ML?
* Low level security quirks
* Compiler basics
* OS design
* Retrocomputing
* git usage
* ... and much more


See [roadmap](#roadmap) for more info.


__**What this project is not about**__:

* Creating a perfect and optimal new architecture for real world usage.
* Replicating existing code. Although at the end of the day it will be influenced and will converge with existing public knowledge, the fun and interesting objetive is "reinventing the wheel for fun" with experimentation and design, not by copying. Let's say "Hey, after all of this work I reached the same conclusion than that other guy invented years ago" and call it a day.
* Show off how skilled you are. Clarity and ease to follow for newcomers willing to learn is the way to go, so avoid complex code when it is not needed, or at least add comments to it.



## Contributions

I started this project as a personal *divertimento*, just to have fun and because I like this kind of stuff. But then I though it would be even better opening it for the public to participate, to share ideas and to learn from each other.

So this is an open self-training project; anyone is invited to join and contribute via Pull Requests o chat discussions (you can join us on Telegram group (https://t.me/opcodeone)). I'll review and accept them if I consider the additions or modifications fit my own "vision" or "taste" for the project.

That doesn't mean I'm the "master" of the project: Although this will be considered the upstream project, every contributor is encouraged to not discard their additions or modifications on their own forks even if these changes are discarded for upstream, since this is a self-learning project, and following different paths or approaches provides value for everyone.

Don't hesitate to ask whatever you don't understand to catch up, we are here to help each other and to learn together at our own pace.



## Getting started


You can start contributing following (but not limited by) these [exercises](EXERCISES.md).

Also don't forget to check the [wiki](https://github.com/MoebiuZ/OpcodeOne/wiki) to find useful/interesting info and references.



## Roadmap


(Order is not strict)

- Design a 24bit architecture: OpcodeOne (O¹)
- Draw a diagram for the fictional physical (hardware) CPU implementation
- Write an assembler/disassembler/debugger
- Design an intermediate language
- Write a compiler (and probably a custom high level language)
- Bare metal ARM11 VM implementation on Raspberry Pi
- Hardware CPU simulator based on RPi (a *big box* with CPU pin out)
- Implement JTAG on hardware CPU simulator
- C++ VM implementation
- WebAssembly VM implementation
- Create a basic OS and software on top of O¹
- Explore flaws on the architecture design and write PoC exploits for them
- Write a graphic adventure (ala Maniac Mansion)
- Redesign architecture to implement security countermeasures
- Write O¹ r_asm/r_anal/r_reg/r_debug [plugins for radare2](https://github.com/radare/radare2/wiki/Implementing-a-new-architecture)
- Study the possibility to implement O¹ on a cheap FPGA
- ...
