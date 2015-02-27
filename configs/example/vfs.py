# Copyright (c) 2009-2011 Advanced Micro Devices, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Brad Beckmann

#
# Full system configuraiton for ruby
#

import optparse
import sys

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.util import addToPath, fatal

addToPath('../common')
addToPath('../ruby')

import Ruby

from FSConfig import *
from SysPaths import *
from Benchmarks import *
import Options
import Simulation

parser = optparse.OptionParser()
Options.addCommonOptions(parser)
Options.addFSOptions(parser)
Options.addVOptions(parser)

# Add the ruby specific and protocol specific options
Ruby.define_options(parser)

(options, args) = parser.parse_args()
options.ruby = True

voptions=[]

if args:
    print "Error: script doesn't take any positional arguments"
    sys.exit(1)

#if options.benchmark:
#    try:
#        bm = Benchmarks[options.benchmark]
#    except KeyError:
#        print "Error benchmark %s has not been defined." % options.benchmark
#        print "Valid benchmarks are: %s" % DefinedBenchmarks
#        sys.exit(1)
#else:
vm_cpus = options.virtual_num_cpus.split("-")
vm_mems = options.virtual_mem_size.split("-")

if len(vm_cpus) != len(vm_mems):
    print "Error: in number of vms. check --virtual-num-cpus and --virtual-mem-size"
    sys.exit(1)

num_vms = len(vm_cpus)

bm = []

for vm_mem in vm_mems:
    bm.append(SysConfig(disk=options.disk_image, mem=vm_mem))

# Check for timing mode because ruby does not support atomic accesses
if not (options.cpu_type == "detailed" or options.cpu_type == "timing"):
    print >> sys.stderr, "Ruby requires TimingSimpleCPU or O3CPU!!"
    sys.exit(1)
(CPUClass, test_mem_mode, FutureClass) = Simulation.setCPUClass(options)

CPUClass.clock = options.clock

systems = []

total_num_cpus = 0
total_mem_size = MemorySize('0B')

for i in xrange(num_vms):
    if buildEnv['TARGET_ISA'] == "alpha":
        systems.append(makeLinuxAlphaRubySystem(test_mem_mode, bm[i]))
    elif buildEnv['TARGET_ISA'] == "x86":
        print "going to append x86"
        systems.append(makeLinuxX86System(test_mem_mode, int(vm_cpus[i]), bm[i], True))
        print "x86 appended"
        Simulation.setWorkCountOptions(systems[i], options)
        print "after set work"
    else:
        fatal("incapable of building non-alpha or non-x86 full system!")

    if options.kernel is not None:
        systems[i].kernel = binary(options.kernel)

    if options.script is not None:
        systems[i].readfile = options.script

    systems[i].cpu = [CPUClass(cpu_id=j) for j in xrange(int(vm_cpus[i]))]
    total_num_cpus += int(vm_cpus[i])
    total_mem_size.value += MemorySize(vm_mems[i]).value

#FIXME
print "before creating ruby"
ruby = Ruby.create_vsystem(options, systems, total_num_cpus, total_mem_size, vm_cpus, vm_mems)
print "after ruby"


#systems[0].dir_cntrl0.directory.size = options.virtual_mem_size
#system.ruby.mem_size = options.mem_size

k = 0
for j in xrange(num_vms):
    for (i, cpu) in enumerate(systems[j].cpu):
        #
        # Tie the cpu ports to the correct ruby system ports
        #
        cpu.createInterruptController()
        cpu.icache_port = ruby._cpu_ruby_ports[k].slave
        cpu.dcache_port = ruby._cpu_ruby_ports[k].slave
        if buildEnv['TARGET_ISA'] == "x86":
            cpu.itb.walker.port = ruby._cpu_ruby_ports[k].slave
            cpu.dtb.walker.port = ruby._cpu_ruby_ports[k].slave
            cpu.interrupts.pio = systems[j].piobus.master
            cpu.interrupts.int_master = systems[j].piobus.slave
            cpu.interrupts.int_slave = systems[j].piobus.master
        k += 1

#print ruby._parent
#print ".."
#print systems[0]._parent

systems[0].ruby = ruby

print "we are before making root"
root = Root(full_system = True, system = systems[0])

#ruby._parent = systems[0]
#systems[0]._parent = ruby
#systems[1]._parent = root

#ruby.system1 = systems[1]

#root.system1 = systems[1]
#root.ruby = ruby

#systems[0].memories = systems[0].physmem

#root.system1 = systems[1]

#print "we are after making root!"
#root.ruby = ruby
for (i, vm) in enumerate(systems):
   if i != 0:
       exec("root.system%d = systems[i]" % i)

#print root._children

for sys in systems:
    print "..."
    print sys._children
#m5.instantiate()

Simulation.run(options, root, ruby, FutureClass)
