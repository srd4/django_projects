from django.db import models
from django.conf import settings

from django.utils import timezone


class Container(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(max_length=140)
    parentContainer = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lastOpened = models.DateTimeField(default=timezone.now)
    timesOpened = models.IntegerField(default=1)
    collapsed = models.BooleanField(default=True)
    seeingActionables = models.BooleanField(default=True)

    def delete(self, *args, **kwargs):
        #Children containers fall into parent container after their container is deleted.
        for i in self.getChildren():
            i.parentContainer = self.parentContainer
            #children's name is changed to show the relationship that existed.
            i.name = self.name + " : " + i.name
            i.save()

        for i in self.getItems():
            if self.parentContainer != None: #if container has a parentContainer...
                i.parentContainer = self.parentContainer  #such parentContainer is set as each Item's new parentContainer. 
            elif Container.objects.filter(owner=self.owner).exists(): #if there is no parent container and the user owns other containers...
                i.parentContainer = Container.objects.filter(owner=self.owner).first() #first container owned by the user is set as their parent.
            else: #Item's are left out without a parentContainer, -see on_delete in field attribute on 'Item' class.
                pass
            i.save()
        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.name

    def add_timesOpened(self):
        self.timesOpened += 1
        self.save()

    def add_lastOpened(self):
        self.lastOpened = timezone.now()
        self.save()

    def getChildren(self):
        """'order_by' used on templates containersView's template"""
        return Container.objects.filter(parentContainer=self.pk, owner=self.owner).order_by('-timesOpened')

    def getItems(self):
        """return children items."""
        return Item.objects.filter(parentContainer=self.pk, owner=self.owner)

    def toggleCollapsed(self):
        if self.collapsed == True:
            self.collapsed = False
        else:
            self.collapsed = True
        self.save()
    
    def toggleTab(self):
        if self.seeingActionables == True:
            self.seeingActionables = False
        else:
            self.seeingActionables = True
        self.save()

    def countTreeItems(self):
        """recursively count the items on itself and all subcontainers of it's subcontainers"""
        i = len(self.getItems())
        for child in self.getChildren():
            i += child.countTreeItems()
        return i


class Item(models.Model):
    actionable = models.BooleanField(default=False)
    done = models.BooleanField(default=False)
    statement = models.TextField(max_length=140)
    parentContainer = models.ForeignKey(Container, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parentItem = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    completed_at = models.DateTimeField(null=True, default=None)

    def create_ItemStatementVersion(self):
        """creates an ItemStatementVersion object with the statement that the Item currently has on db"""
        current_statement_exists = Item.objects.filter(pk=self.pk, owner=self.owner).exists()
        
        if current_statement_exists: #if this method is not being called for Item creation from self.saved()...
            current_statement = Item.objects.get(pk=self.pk, owner=self.owner).statement
            #get_or_create helps with not repeating an instance that already exists.
            return ItemStatementVersion.objects.get_or_create(statement=current_statement, defaults={"created_at" : self.updated_at, "parentItem": self,  "owner":self.owner})
        return None


    def save(self, *args, **kwargs):
        """creates ItemStatementVersion objects before saving"""
        self.create_ItemStatementVersion()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.statement

    def get_parentContainer(self):
        """returns parentContainer object as currently in db"""
        #to control objects.get() method's expection. None as pk is not a problem for filter() method.
        parentContainer_exists = Container.objects.filter(pk=self.parentContainer.pk, owner=self.owner).exists()

        if parentContainer_exists:
            return Container.objects.get(pk=self.parentContainer.pk, owner=self.owner)
        return None
    
    def get_parentItem(self):
        """returns parentItem object as currently in db"""
        #to control objects.get() method's expection. None as pk is not a problem for filter() method.
        parentItem_exists = Item.objects.filter(pk=self.parentItem.pk, owner=self.owner).exists()

        if parentItem_exists:
            return Item.objects.get(pk=self.parentItem.pk, owner=self.owner)
        return None

    def get_versions(self):
        return ItemStatementVersion.objects.filter(parentItem=self, owner=self.owner)

    def toggleDone(self):
        """called from views and templates to make self.done values change"""
        if self.done:
            self.done = False
            self.completed_at = None
        else:
            self.done = True
            self.completed_at = timezone.now()
        self.save()
        
        return self.done


class ItemStatementVersion(models.Model):
    statement = models.TextField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True)
    parentItem = models.ForeignKey(Item, null=True, on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.statement