# BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2005 Michael "ThorN" Thornton
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

__author__  = 'xlr8or'
__version__ = '1.0.0'

import b3.parsers.cod2
import b3.parsers.q3a
import b3.functions
import re, threading

class Cod5Parser(b3.parsers.cod2.Cod2Parser):
    gameName = 'cod5'

    # join
    def OnJ(self, action, data, match=None):
        codguid = match.group('guid')
        cid = match.group('cid')
        name = match.group('name')
        
        #CoD:WaW has a 10 number guid, don't you just love it when they change everything at each release? 
        if len(codguid) < 10:
            # invalid guid
            codguid = None

        client = self.getClient(match)

        if client:
            # update existing client
            client.state = b3.STATE_ALIVE
            # possible name changed
            client.name = match.group('name')
            # Join-event for mapcount reasons and so forth
            return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)
        else:
            t = threading.Timer(2, self.newPlayer, (cid, codguid, name))
            t.start()
            self.debug('%s connected, waiting for Authentication...' %name)                


    # kill
    def OnK(self, action, data, match=None):
        victim = self.getClient(victim=match)
        if not victim:
            self.debug('No victim %s' % match.groupdict())
            self.OnJ(action, data, match)
            return None

        attacker = self.getClient(attacker=match)
        if not attacker:
            self.debug('No attacker %s' % match.groupdict())
            return None

        # COD4 doesn't report the team on kill, only use it if it's set
        # Hopefully the team has been set on another event
        if match.group('ateam'):
            attacker.team = self.getTeam(match.group('ateam'))

        if match.group('team'):
            victim.team = self.getTeam(match.group('team'))


        attacker.name = match.group('aname')
        victim.name = match.group('name')

        event = b3.events.EVT_CLIENT_KILL

        if attacker.cid == victim.cid:
            event = b3.events.EVT_CLIENT_SUICIDE
        elif attacker.team != b3.TEAM_UNKNOWN and \
             attacker.team and \
             victim.team and \
             attacker.team == victim.team:
            event = b3.events.EVT_CLIENT_KILL_TEAM

        victim.state = b3.STATE_DEAD
        return b3.events.Event(event, (float(match.group('damage')), match.group('aweap'), match.group('dlocation'), match.group('dtype')), attacker, victim)

    def connectClient(self, ccid):
        players = self.getPlayerList()
        self.verbose('connectClient() = %s' % players)

        for cid, p in players.iteritems():
            #self.debug('cid: %s, ccid: %s, p: %s' %(cid, ccid, p))
            if int(cid) == int(ccid):
                self.debug('Client found in status/playerList')
                return p

    def newPlayer(self, cid, codguid, name):
        self.debug('newClient: %s, %s, %s' %(cid, codguid, name) )
        sp = self.connectClient(cid)
        # PunkBuster is enabled, using PB guid
        if sp and self.PunkBuster:
            self.debug('sp: %s' % sp)
            guid = sp['pbid']
            ip = sp['ip']
        # PunBuster is not enabled, using codguid
        elif sp:
            guid = codguid
            ip = sp['ip']
        # Player is not in the status response (yet), retry
        else:
            self.debug('Player not yet fuly connected, retrying...')
            t = threading.Timer(2, self.newPlayer, (cid, codguid, name))
            t.start()
            return None
            
        client = self.clients.newClient(cid, name=name, ip=ip, state=b3.STATE_ALIVE, guid=guid, data={ 'codguid' : codguid })
        return b3.events.Event(b3.events.EVT_CLIENT_JOIN, None, client)