#!/bin/bash
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

# Descriptive name for the current results
UNDERTEST_NAME=${TENSORRT_SERVER_VERSION}

# Descriptive name and subdirectory containing results to compare
# against.
BASELINE_NAME=19.07
BASELINE_DIR=1907_results

# Set the confidence percentile to use when stabilizing and reporting
# results.
PERF_CLIENT_PERCENTILE=95

RUNTEST=./runtest.sh
ANALYZETEST=./perf_analysis.py

RET=0

set +e

# Run to get minimum latency results. This uses batch-size 1 and a
# single model instance.
MIN_LATENCY_GRPC_DIR=min_latency_grpc
MIN_LATENCY_GRPC_NAME="${UNDERTEST_NAME} Minimum Latency GRPC"
rm -fr ./${MIN_LATENCY_GRPC_DIR}
RESULTNAME=${MIN_LATENCY_GRPC_NAME} \
          RESULTDIR=./${MIN_LATENCY_GRPC_DIR} \
          PERF_CLIENT_PERCENTILE=${PERF_CLIENT_PERCENTILE} \
          PERF_CLIENT_PROTOCOL=grpc \
          STATIC_BATCH_SIZES=1 \
          DYNAMIC_BATCH_SIZES=1 \
          INSTANCE_COUNTS=1 \
          REQUIRED_MAX_CONCURRENCY=1 \
          bash -x ${RUNTEST}
if (( $? != 0 )); then
    RET=1
fi

MIN_LATENCY_HTTP_DIR=min_latency_http
MIN_LATENCY_HTTP_NAME="${UNDERTEST_NAME} Minimum Latency HTTP"
rm -fr ./${MIN_LATENCY_HTTP_DIR}
RESULTNAME=${MIN_LATENCY_HTTP_NAME} \
          RESULTDIR=./${MIN_LATENCY_HTTP_DIR} \
          PERF_CLIENT_PERCENTILE=${PERF_CLIENT_PERCENTILE} \
          PERF_CLIENT_PROTOCOL=http \
          STATIC_BATCH_SIZES=1 \
          DYNAMIC_BATCH_SIZES=1 \
          INSTANCE_COUNTS=1 \
          REQUIRED_MAX_CONCURRENCY=1 \
          bash -x ${RUNTEST}
if (( $? != 0 )); then
    RET=1
fi

# Compare minimum latency results against baseline.
$ANALYZETEST --latency \
             --baseline-name=${BASELINE_NAME} \
             --baseline=${BASELINE_DIR}/${MIN_LATENCY_GRPC_DIR} \
             --undertest-name=${UNDERTEST_NAME} \
             --undertest=${MIN_LATENCY_GRPC_DIR}
if (( $? != 0 )); then
    echo -e "** ${MIN_LATENCY_GRPC_NAME} Analysis Failed"
    RET=1
fi

set -e

if (( $RET == 0 )); then
    echo -e "\n***\n*** Test Passed\n***"
else
    echo -e "\n***\n*** Test FAILED\n***"
fi

exit $RET
