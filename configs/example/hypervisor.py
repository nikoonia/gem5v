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
addToPath('../topologies')

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

vm_mems = options.vm_mem_sizes.split(":")
vm_scripts = options.vm_scripts.split(":")
vm_cpu_placement = options.vm_cpu_placements.split(":")

if len(vm_mems) != len(vm_cpu_placement):
    print "Error: in number of vms. check --vm-cpu-placements and --vm-mem-sizes"
    sys.exit(1)

if len(vm_mems) != len(vm_scripts):
    print "Error: number of vm scripts should be equal to number of vms"
    sys.exit(1)

vmm_cpu_matrix = []


for (i, vm_cpu) in enumerate(vm_cpu_placement):
    vmm_cpu_matrix.append(vm_cpu.split("-"))
    if len(vmm_cpu_matrix[i]) != len(vmm_cpu_matrix[0]):
        print "Error in VM#%d" % i
        print "check --vm-cpu-placements"
        sys.exit(1)

for i in xrange(len(vmm_cpu_matrix[0])):
    cpu_load = 0
    for j in xrange(len(vmm_cpu_matrix)):
        cpu_load += float(vmm_cpu_matrix[j][i])
    if cpu_load != 1:
        print "Load error for cpu#%d" % i
        print "load is %f" % cpu_load
        sys.exit(1)

vm_cpus = []

for i in xrange(len(vmm_cpu_matrix)):
    vm_cpus.append(0)
    for j in xrange(len(vmm_cpu_matrix[i])):
        if vmm_cpu_matrix[i][j] != "0":
            vm_cpus[i] += 1
            #print "vm cpus %d " % vm_cpus[i]

#for x in vm_cpus:
#    print "X %d" % x

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
        systems.append(makeLinuxX86System(test_mem_mode, vm_cpus[i], bm[i], True))
        Simulation.setWorkCountOptions(systems[i], options)
    else:
        fatal("incapable of building non-alpha or non-x86 full system!")

    if options.kernel is not None:
        systems[i].kernel = binary(options.kernel)

    if vm_scripts[i] != "":
        systems[i].readfile = vm_scripts[i]

    systems[i].cpu = [CPUClass(cpu_id=j) for j in xrange(vm_cpus[i])]
    total_num_cpus += int(vm_cpus[i])
    total_mem_size.value += MemorySize(vm_mems[i]).value

print total_mem_size

assert(options.vm_context_switch_hyperperiod > 0)

for i in xrange(num_vms):
    #print "X %d " % i
    cpu_index = 0
    for j in xrange(len(vmm_cpu_matrix[i])):
        if vmm_cpu_matrix[i][j] == "0":
            continue
        #print "i am here"
        cpu_accumulated = 0.0
        for k in xrange(i+1):
            cpu_accumulated += float(vmm_cpu_matrix[k][j])
            print "acc %f " % cpu_accumulated
            print float(vmm_cpu_matrix[k][j]) + 1
            print vmm_cpu_matrix[k][j]
        if float(vmm_cpu_matrix[i][j]) > 0 and float(vmm_cpu_matrix[i][j]) < 1: 
            systems[i].cpu[cpu_index].vcpu = True
            systems[i].cpu[cpu_index].vcpu_hyperperiod = options.vm_context_switch_hyperperiod
            systems[i].cpu[cpu_index].vcpu_stop_tick = options.vm_context_switch_hyperperiod*cpu_accumulated
            print systems[i].cpu[cpu_index].vcpu_stop_tick
            systems[i].cpu[cpu_index].vcpu_start_tick = options.vm_context_switch_hyperperiod*cpu_accumulated - options.vm_context_switch_hyperperiod*float(vmm_cpu_matrix[i][j]) + options.vm_context_switch_overhead
            print "hyper period %d" % systems[i].cpu[cpu_index].vcpu_hyperperiod
            print "start %d" % systems[i].cpu[cpu_index].vcpu_start_tick
            print "stop %d" % systems[i].cpu[cpu_index].vcpu_stop_tick
            #assert(systems[i].cpu[cpu_index].vcpu_start_tick < systems[i].cpu[cpu_index].vcpu_stop_tick)
        if cpu_accumulated > 0:
            cpu_index += 1
            #print "cpu index = %d" % cpu_index


#print "before creating ruby"
ruby = Ruby.create_vsystem(options, systems, total_num_cpus, total_mem_size, vm_cpus, vm_mems, vmm_cpu_matrix)
#print "after ruby"


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

#print "we are before making root"
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

#for sys in systems:
#    print "..."
#    print sys._children
#m5.instantiate()

#added to deal with
#panic: Can’t create socket:Too many open files !

#m5.disableAllListeners()

Simulation.run(options, root, ruby, FutureClass)
