"""Publish current frequency/band without transient slice-change relay storms."""

import time
import logging

LOG = logging.getLogger('flex.band')


class BandPublisher:
    def __init__(self, station, publish, band_for_frequency, clock=time.monotonic):
        self.station = station
        self.publish = publish
        self.band_for_frequency = band_for_frequency
        self.clock = clock
        self.missing_since = None
        self.last_band = None
        self.last_qrg = None
        self.band_time = 0
        self.qrg_time = 0

    def update(self, frequency):
        now = self.clock()
        if frequency is None:
            if self.missing_since is None:
                self.missing_since = now
            # Slice recreation briefly removes the active slice during a band change.
            if now - self.missing_since < 2:
                return
            band, qrg = 0, 0
        else:
            self.missing_since = None
            frequency = float(frequency)
            band, qrg = self.band_for_frequency(frequency), frequency * 100000
        if qrg != self.last_qrg or now - self.qrg_time >= 2:
            self.publish(f'{self.station}/qrg', str(qrg))
            self.last_qrg, self.qrg_time = qrg, now
        if band != self.last_band or now - self.band_time >= 2:
            if band != self.last_band:
                LOG.info('%s banda=%s frecuencia=%s MHz', self.station, band, frequency if frequency is not None else 'sin datos')
            self.publish(f'{self.station}/band', str(band))
            self.last_band, self.band_time = band, now
