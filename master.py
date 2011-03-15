# -*- python -*-
# ex: set syntax=python:

c = BuildmasterConfig = {}
####### BUILDSLAVES
from buildbot.buildslave import BuildSlave
slave_names = {
	'x86_64-win32': ['sdwilsh-windows%i' % x for x in range(1,5)],
        'x86-fedora': ['johnford.info-slave1'],
	'x86-freebsd': ['robarnold-freebsd'],
}
slaves = {}
c['slaves'] = []
for platform in slave_names.keys():
    slaves[platform] = []
    for i in slave_names[platform]:
      slave = BuildSlave(i, "password", max_builds=1)
      slaves[platform].append(slave)
      c['slaves'].append(slave)
c['slavePortnum'] = 9989

####### CHANGESOURCES
#from buildbot.changes.gitpoller import GitPoller
#c['change_source'] = GitPoller(
#        'git://github.com/zpao/v8monkey.git',
#        branch='master', pollinterval=600)


####### BUILDERS
from buildbot.process.factory import BuildFactory
from buildbot.steps.source import Git
from buildbot.steps.shell import Configure, Compile, ShellCommand

factory = BuildFactory()
# check out the source
factory.addStep(ShellCommand(command=['rm', '-rf', 'objdir'], workdir="."))
factory.addStep(Git(repourl='git://github.com/zpao/v8monkey.git', mode='copy'))
factory.addStep(ShellCommand(command="bash -c autoconf-2.13", workdir="build/js/src"))
factory.addStep(Configure(command="bash -c ../build/js/src/configure", workdir="objdir"))
factory.addStep(Compile(workdir="objdir"))

from buildbot.config import BuilderConfig

c['builders'] = []
branch_builders = []
for platform in slave_names.keys():
    builder_name = "%s-build" % platform
    branch_builders.append(builder_name)
    c['builders'].append(
        BuilderConfig(name=builder_name,
         slavenames=slave_names[platform],
         factory=factory))

####### SCHEDULERS
from buildbot.scheduler import Scheduler
c['schedulers'] = []
c['schedulers'].append(Scheduler(name="all", branch='master',
                                 treeStableTimer=None,
                                 builderNames=branch_builders))
####### STATUS TARGETS

# 'status' is a list of Status Targets. The results of each build will be
# pushed to these targets. buildbot/status/*.py has a variety to choose from,
# including web pages, email senders, and IRC bots.

c['status'] = []

from buildbot.status import html
from buildbot.status.web import auth, authz
authz_cfg=authz.Authz(
    # change any of these to True to enable; see the manual for more
    # options
    gracefulShutdown = False,
    forceBuild = True, # use this to test your slave once it is set up
    forceAllBuilds = False,
    pingBuilder = False,
    stopBuild = False,
    stopAllBuilds = False,
    cancelPendingBuild = False,
)
notify_events={'successToFailure': 1,
               'failureToSuccess': 1,
               'exception': 1,
}
c['status'].append(html.WebStatus(http_port=8010, authz=authz_cfg,
                                  change_hook_dialects={'github': True}))


from buildbot.status.words import IRC
c['status'].append(IRC(host='irc.mozilla.org', nick='gertrude', 
                       channels=['#spidernode'], port=6697, useSSL=True,
                       notify_events=notify_events))


#from buildbot.status.mail import MailNotifier
#c['status'].append(MailNotifier(fromaddr="gertrude@johnford.info",
#                                sendToInterestedUsers=False,
#                                extraRecipients=['listaddr'])

####### PROJECT IDENTITY

# the 'projectName' string will be used to describe the project that this
# buildbot is working on. For example, it is used as the title of the
# waterfall HTML page. The 'projectURL' string will be used to provide a link
# from buildbot HTML pages to your project's home page.

c['projectName'] = "spidernode"
c['projectURL'] = "https://github.com/zpao/v8monkey"

# the 'buildbotURL' string should point to the location where the buildbot's
# internal web server (usually the html.WebStatus page) is visible. This
# typically uses the port number set in the Waterfall 'status' entry, but
# with an externally-visible host name which the buildbot cannot figure out
# without some help.

c['buildbotURL'] = "http://johnford.info:8010/"

####### DB URL

# This specifies what database buildbot uses to store change and scheduler
# state.  You can leave this at its default for all but the largest
# installations.
c['db_url'] = "sqlite:///state.sqlite"

