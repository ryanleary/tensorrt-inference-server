#!/usr/bin/python

# Copyright (c) 2019, NVIDIA CORPORATION. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of NVIDIA CORPORATION nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
from builtins import range
import csv
import os
import sys

FLAGS = None
CONCURRENCY = "Concurrency"
INFERPERSEC = "Inferences/Second"

def read_results(concurrency, path):
    """
    Create a map from model type (i.e. platform) to map from CSV file
    heading to value at the given concurrency level.
    """
    csvs = dict()
    for f in os.listdir(path):
        fullpath = os.path.join(path, f)
        if os.path.isfile(fullpath) and (f.endswith(".csv")):
            platform = f.split('_')[0]
            csvs[platform] = fullpath

    results = dict()
    for platform, fullpath in csvs.items():
        with open(fullpath, "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            linenum = 0
            header_row = None
            concurrency_row = None
            for row in csv_reader:
                if linenum == 0:
                    header_row = row
                else:
                    if int(row[0]) == concurrency:
                        concurrency_row = row
                        break

                linenum += 1

            if (header_row is None) or (concurrency_row is None):
                print("warning: unable to parse CSV file {}".format(fullpath))

            results[platform] = dict()
            for header, result in zip(header_row, concurrency_row):
                results[platform][header] = result

    return results

def lower_is_better(name):
    return name != INFERPERSEC

def get_delta(name, baseline, result):
    if lower_is_better(name):
        speedup = float(baseline) / float(result)
    else:
        speedup = float(result) / float(baseline)

    delta = (speedup * 100.0) - 100.0

    GREEN = '\033[92m'
    RED = '\033[91m'
    ENDC = '\033[0m'

    color = RED if delta < 0 else GREEN if delta > 0 else ENDC
    return "{}{:.2f}%{}".format(color, delta, ENDC)

def latency_analysis(baseline_name, undertest_name,
                     baseline_results, undertest_results):
    """
    Compare baseline and under-test results and report on any +/- in
    latency.
    """
    for platform, undertest_result in undertest_results.items():
        print("\n{}\n{}".format(platform, '-' * len(platform)))
        print("{:>40}{:>12}".format(baseline_name, undertest_name))

        baseline_result = None
        if platform in baseline_results:
            baseline_result = baseline_results[platform]

        if ((baseline_result is not None) and
            (CONCURRENCY in baseline_result) and
            (CONCURRENCY in undertest_result) and
            (baseline_result[CONCURRENCY] != undertest_result[CONCURRENCY])):
            print("warning: baseline concurrency {} != under-test concurrency {}".
                  format(baseline_result[CONCURRENCY], undertest_result[CONCURRENCY]))

        ordered_names = [n for n in undertest_result
                         if (n != CONCURRENCY) and (n != INFERPERSEC) ]
        ordered_names.sort()
        ordered_names.append(INFERPERSEC)

        for name in ordered_names:
            result = undertest_result[name]
            if (baseline_result is None) or (name not in baseline_result):
                print("{:<28}{:>12}{:>12}".format(name, "<none>", result))
            else:
                delta = get_delta(name, baseline_result[name], result)
                print("{:<28}{:>12}{:>12}{:>20}".format(name, baseline_result[name], result, delta))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action="store_true", required=False, default=False,
                        help='Enable verbose output.')
    parser.add_argument('--latency', action="store_true", required=False, default=False,
                        help='Perform latency analysis.')
    parser.add_argument('--throughput', action="store_true", required=False, default=False,
                        help='Perform throughput analysis.')
    parser.add_argument('--concurrency', type=int, required=False,
                        help='Use specific concurrency level for analysis. If not ' +
                        'specified an appropriate concurrency level will be selected ' +
                        'automatically.')
    parser.add_argument('--baseline-name', type=str, required=True,
                        help='Descriptive name of the baseline being compared against.')
    parser.add_argument('--baseline', type=str, required=True,
                        help='Path to the directory containing baseline results.')
    parser.add_argument('--undertest-name', type=str, required=True,
                        help='Descriptive name of the results being analyzed.')
    parser.add_argument('--undertest', type=str, required=True,
                        help='Path to the directory containing results being analyzed.')

    FLAGS = parser.parse_args()

    # Latency analysis. Use concurrency 1 unless an explicit
    # concurrency is requested.
    if FLAGS.latency:
        concurrency = 1 if FLAGS.concurrency is None else FLAGS.concurrency
        baseline_results = read_results(concurrency, FLAGS.baseline)
        undertest_results = read_results(concurrency, FLAGS.undertest)
        latency_analysis(FLAGS.baseline_name, FLAGS.undertest_name,
                         baseline_results, undertest_results)
