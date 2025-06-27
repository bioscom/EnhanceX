from simple_menu import Menu, MenuItem
from django.urls import reverse

# Add two items to our main menu
Menu.add_item("main", MenuItem("Tools", reverse("myapp.views.tools"), weight=10, icon="tools"))

Menu.add_item("main", MenuItem("Reports", reverse("myapp.views.reports"), weight=20, icon="report"))


# Define children for the my account menu
myaccount_children = (MenuItem("Edit Profile", reverse("accounts.views.editprofile"), weight=10, icon="user"),
    MenuItem("Admin", reverse("admin:index"), weight=80, separator=True, check=lambda request: request.user.is_superuser),
    MenuItem("Logout", reverse("accounts.views.logout"), weight=90, separator=True, icon="user"),
)

# Add a My Account item to our user menu
Menu.add_item("user", MenuItem("My Account", reverse("accounts.views.myaccount"), weight=10, children=myaccount_children))



from utils.menus import ViewMenuItem

from simple_menu import Menu, MenuItem

from django.core.urlresolvers import reverse

# Since we use ViewMenuItem here we do not need to define checks, instead
# the check logic will change their visibility based on the permissions
# attached to the views we reverse here.
reports_children = (
     ViewMenuItem("Staff Only", reverse("reports.views.staff")),
     ViewMenuItem("Superuser Only", reverse("reports.views.superuser"))
)

Menu.add_item("main", MenuItem("Reports Index",
                               reverse("reports.views.index"),
                               children=reports_children))