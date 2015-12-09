from itertools import repeat
from uuid import uuid4
from ipaddr import IPAddress
import math
from twisted.internet.defer import succeed
from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase

from flocker.apiclient._client import FakeFlockerClient, Node

from benchmark.scenarios import (
    ReadRequestLoadScenario, RateMeasurer, RequestRateTooLow
)

from benchmark.cluster import BenchmarkCluster


class RateMeasurerTest(SynchronousTestCase):
    """
    RateMeasurer tests
    """

    def test_rate_is_nan_when_no_samples(self):
        """
        """
        r = RateMeasurer(Clock())
        self.assertTrue(math.isnan(r.rate()))

    def test_rate_is_nan_when_not_enough_samples(self):
        """
        """
        c = Clock()
        r = RateMeasurer(c)

        r.new_sample()
        c.advance(1)

        self.assertTrue(math.isnan(r.rate()))

    def test_rate_is_correct_when_enough_samples(self):
        """
        """
        c = Clock()
        sample_size = 2
        r = RateMeasurer(c, sample_size=sample_size)

        # Advance by sample size + 1 because the RateMeasurer only knows
        # that time has passed when new_sample is called.
        for i in xrange(sample_size + 1):
            r.new_sample()
            c.advance(1)

        # TODO: Should this be assertAlmostEqual? Will this pass
        # everywhere? We are suspicious of floating point comparisons
        self.assertEqual(r.rate(), 1.0)

    def test_old_samples_are_not_considered(self):
        """
        """
        c = Clock()
        sample_size = 2
        r = RateMeasurer(c, sample_size=sample_size)

        # Create a rate of 1.0
        for i in xrange(sample_size):
            r.new_sample()
            c.advance(1)

        # Create a rate of 2.0
        for i in xrange(sample_size + 1):
            r.new_sample()
            r.new_sample()
            c.advance(1)

        self.assertEqual(r.rate(), 2.0)


class RequestDroppingFakeFlockerClient(FakeFlockerClient):
    """
    A FakeFlockerClient that can drop alternating requests.
    """
    def __init__(self, nodes, drop_requests=False):
        super(RequestDroppingFakeFlockerClient, self).__init__(nodes)
        self.drop_requests = drop_requests
        self._dropped_last_request = False

    def list_nodes(self):
        if not self.drop_requests:
            return succeed(True)
        else:
            if self._dropped_last_request:
                self._dropped_last_request = False
                return succeed(True)
            self._dropped_last_request = True


class ReadRequestLoadScenarioTest(SynchronousTestCase):
    """
    ReadRequestLoadScenario tests
    """
    def make_cluster(self, FlockerClient):
        """
        Create a cluster that can be used by the scenario tests.
        """
        # TODO I dont know what is the convention putting braces
        # and splitting a function call between different
        # lines when it is too long
        node1 = Node(uuid=uuid4(), public_address=IPAddress('10.0.0.1'))
        node2 = Node(uuid=uuid4(), public_address=IPAddress('10.0.0.2'))
        return BenchmarkCluster(
            node1.public_address,
            lambda reactor: FlockerClient([node1, node2]),
            {node1.public_address, node2.public_address},
        )

    def test_read_request_load_succeeds(self):
        """
        ReadRequestLoadScenario starts and stops without collapsing.
        """
        c = Clock()
        cluster = self.make_cluster(FakeFlockerClient)
        s = ReadRequestLoadScenario(c, cluster, 5, interval=1)

        d = s.start()
        # TODO: Add comment here to explain these numbers
        # The interval is 5, so in order to register a rate,
        # we need to start the next interval, as when starting
        # a new interval is when we will store the last result
        # of the previous interval (we will store what happened
        # in 5, in 5+1 = 6)
        c.pump(repeat(1, 6))
        s.maintained().addBoth(lambda x: self.fail())
        d.addCallback(lambda ignored: s.stop())
        self.successResultOf(d)

    def test_scenario_throws_exception_when_rate_drops(self):
        """
        ReadRequestLoadScenario raises RequestRateTooLow if rate
        drops below the requested rate.

        Establish the requested rate by having the FakeFlockerClient
        repond to all requests. Then attempt to lower the rate by
        dropping alternate requests. This should result in
        RequestRateTooLow being raised.
        """
        c = Clock()
        cluster = self.make_cluster(RequestDroppingFakeFlockerClient)
        s = ReadRequestLoadScenario(c, cluster, 5, interval=1)

        s.start()
        # TODO: Add comment here to explain these numbers
        c.pump(repeat(1, 6))

        cluster.get_control_service(c).drop_requests = True
        c.pump(repeat(1, 3))

        failure = self.failureResultOf(s.maintained())
        self.assertIsInstance(failure.value, RequestRateTooLow)
