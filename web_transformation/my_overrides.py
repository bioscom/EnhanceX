from django_sso.sso_service.backends import EventAcceptor, acceptor

# In case, when you need to do something after deauthentication
class MyEventAcceptor(EventAcceptor):
    @acceptor # Every event accpetor method must be decorated with it
    def deauthenticate(self, username):
        # Here you can do own actions before deauthentication
        super().deauthenticate(username)
        # And here you can do own actions after deauthentication

        
# In other case, when you need to override default behavior of class
class MyHardEventAcceptor(EventAcceptor):
    @acceptor
    def deauthenticate(self, username):
        # Here you do own actionsr