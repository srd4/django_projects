from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from .models import Container, Item
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django import forms
from django.db.models import Q
from django.contrib.auth.views import LoginView, LogoutView

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

LoginRequiredMixin.login_url = reverse_lazy('notebook_2:login')

def itemDone(request, pk):
    i = Item.objects.get(pk=pk, owner=request.user)
    i.toggleDone()
    return render(request, 'notebook_2/item.html', {'container':i.parentContainer, 'item':i})


def containerCollapse(request, pk):
    """toggles collapsed or not on containersView"""
    c = Container.objects.get(pk=pk, owner=request.user)
    c.toggleCollapsed()
    return render(request, 'notebook_2/containersList.html', {'container_list':[c,]})


def containerChangeTab(request, pk):
    """toggles action or non-actionable or not on containerDetailView"""
    c = Container.objects.get(pk=pk, owner=request.user)
    if request.GET.get('toggle') == "True":
        c.toggleTab()
    item_list = c.getItems().order_by('done', '-updated_at') #all done go bottom, most recently created on top.
    return render(request, 'notebook_2/itemList.html', {'item_list': item_list, 'container': c})


class loginView(LoginView):
    template_name = "notebook_2/login.html"
    success_url = reverse_lazy('notebook_2:containers')
    redirect_authenticated_user = True


class logoutView(LogoutView):
    next_page = reverse_lazy('notebook_2:login')


class registerView(FormView):
    form_class = UserCreationForm
    template_name = "notebook_2/register.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        User = form.save() #creates and saves user to database.
        if User is not None:
            login(self.request, User)
        return super(registerView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        #page title that is rendered to main.html on <title> tag.
        ctx["view_title"] = "Registration"
        return ctx

    def get(self, *args, **kwargs):
        """redirects authenticated user to 'home'"""
        if self.request.user.is_authenticated:
            return redirect('notebook_2:containers')
        return super(registerView, self).get(self)


class searchView(LoginRequiredMixin, generic.TemplateView):
    template_name = "notebook_2/searchView.html"

    def get_context_data(self):
        searchInput = self.request.GET.get('search_query')

        cqs = Container.objects.all()
        iqs = Item.objects.all()
        cqs = cqs.filter(Q(Q(name__icontains=searchInput) | Q(description__icontains=searchInput)), owner=self.request.user)
        iqs = iqs.filter(Q(statement__icontains=searchInput), owner=self.request.user)

        return {"container_list":cqs, "item_list":iqs, "view_title": "Search"}


class containersView(LoginRequiredMixin, generic.TemplateView):
    model = Container
    template_name = 'notebook_2/containers.html'
    context_object_name = 'container_list'
    
    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        #returns containers that don't have parents sorted by -timesOpened. so the most recently opened go on top.
        ctx["container_list"] = Container.objects.filter(parentContainer=None, owner=self.request.user).order_by('-timesOpened')
        return ctx


class containerDetailView(LoginRequiredMixin, generic.ListView):
    model = Container
    template_name = 'notebook_2/containerDetail.html'
    context_object_name = 'item_list'

    def get_queryset(self):
        #this is the pk that is part of the url, which references the container...
        container_pk = self.kwargs['pk']
        #...that we return the items of.
        return Item.objects.filter(parentContainer=container_pk, owner=self.request.user)

    def get_context_data(self, **kwargs):
        container_pk = self.kwargs['pk']
        c = Container.objects.get(pk=container_pk, owner=self.request.user)
        c.add_lastOpened()
        c.add_timesOpened()
        #container needed to retrieve information on container detail view.
        #item_list corresponding to container, see get_queryset method above this one.
        return {"container": c}

class containerCreateView(LoginRequiredMixin, CreateView):
    model = Container
    template_name = 'notebook_2/containerCreate.html'
    fields = ["name", "description", "parentContainer"]
    success_url = reverse_lazy('notebook_2:containers')

    def get_form(self):
        form = super(containerCreateView, self).get_form()
        #make parent container not required. but appear.
        a_field = form.fields["parentContainer"]
        a_field.required = False
        #limit Container foreignkey options to pick from to containers the user owns.
        a_field.queryset = Container.objects.filter(owner=self.request.user)
        return form

    def form_valid(self, form):
        a_container = form.save(commit=False)
        #save container with owner foreignkey to user who was logged in on its creation.
        a_container.owner = self.request.user
        a_container.save()
        return super(containerCreateView, self).form_valid(form)


class containerUpdateView(LoginRequiredMixin, UpdateView):
    model = Container
    template_name = 'notebook_2/containerUpdate.html'
    context_object_name = 'container_list'
    fields = ["name", "description", "parentContainer"]
    success_url = reverse_lazy('notebook_2:containers')

    def get_form(self):
        form = super(containerUpdateView, self).get_form()
        a_field = form.fields["parentContainer"]
        a_field.required = False
        #excludes itself from query set to select from -container shouldn't be subcontainer of itself. 
        a_field.queryset = Container.objects.filter(owner=self.request.user).exclude(pk=self.kwargs['pk'])
        return form


class containerDeleteView(LoginRequiredMixin, DeleteView):
    model = Container
    template_name = 'notebook_2/containerDelete.html'
    context_object_name = 'container_list'
    success_url = reverse_lazy("notebook_2:containers")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        #only to pass container in context to render template with container name.
        #checking it is the user's.
        ctx['container'] = Container.objects.get(pk=self.kwargs['pk'], owner=self.request.user).name
        return ctx


class itemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    template_name = 'notebook_2/itemCreate.html'
    fields = ["done", "parentContainer", "parentItem", "statement", "actionable"]
    
    def get_success_url(self):
        container_pk = self.request.GET.get('container_pk')
        #if container_pk is passed on get request as query,
        #and such entry exists for current particular user
        if container_pk != "" and Container.objects.filter(pk=container_pk, owner=self.request.user).exists():
            #we go to its containerDetailView.
            return reverse_lazy("notebook_2:container_detail", kwargs={'pk': container_pk})
        #or to the containersView otherwise.
        return reverse_lazy("notebook_2:containers") 
    
    def get_context_data(self, *args, **kwargs):
        ctx = super(itemCreateView, self).get_context_data( *args,**kwargs)

        container_pk = self.request.GET.get('container_pk')
        if container_pk != "": #handling case where there is no container_pk to pass a container to context.
            ctx['container'] = Container.objects.get(pk=container_pk, owner=self.request.user) #user-owned container to populate themplate.

        return ctx

    def get_form(self):
        f = super(itemCreateView, self).get_form()
        container_list = Container.objects.filter(owner=self.request.user) #prepopulating parentContainer field. and limiting queryset to user-owned Containers.

        
        container_pk = self.request.GET.get('container_pk')
        f.fields['parentContainer'].initial = container_pk if container_pk != "" else None #handling case where there is no container_pk to prepopulate the field.
        f.fields["parentContainer"].queryset = Container.objects.filter(owner=self.request.user)

        f.fields['parentItem'].required = False
        f.fields['parentItem'].initial = self.request.GET.get('pk')
        f.fields['parentItem'].widget = forms.HiddenInput()

        #prepopulate actionable field with what's on query.
        f.fields['actionable'].initial = True if self.request.GET.get('actionable') == "True" else False

        return f

    def form_valid(self, form):
        i = form.save(commit=False)
        i.owner = self.request.user #set item as owned by the user who was logged in on creation and saving it.
        i.save()
        return super(itemCreateView, self).form_valid(form)


class itemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    template_name = 'notebook_2/itemUpdate.html'
    fields = ["done", "parentContainer", "parentItem", "statement", "actionable"]

    def get_success_url(self):
        #as you can only see items from containers, container must exist.
        #so we use that Container's detail view as succes_url.
        success_url = reverse_lazy("notebook_2:container_detail", kwargs={'pk': self.request.GET.get('container_pk')})
        return success_url

    def get_context_data(self, *args, **kwargs):
        ctx = super(itemUpdateView, self).get_context_data(*args,**kwargs)
        #getting item we want to update.
        item = Item.objects.get(pk=self.kwargs['pk'], owner=self.request.user)
        #using the item to pass the container to populate some stuff on form template.
        ctx['container'] = item.parentContainer
        return ctx

    def get_form(self):
        f = super(itemUpdateView, self).get_form()
        
        f.fields['parentItem'].required = False #hiddes parentitem input.
        f.fields['parentItem'].widget = forms.HiddenInput() #and sets it as not required (user has to delete and create a different instance to change it)
        return f

    


class itemDeleteView(LoginRequiredMixin, DeleteView):
    model = Item
    template_name = 'notebook_2/itemDelete.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(itemDeleteView, self).get_context_data(*args,**kwargs)
        item = Item.objects.get(pk=self.kwargs['pk'], owner=self.request.user) #using pk on link, making sure it is owned by user.
        ctx['container'] = item.parentContainer #passin container to populate form.

        return ctx
    
    def get_success_url(self):
        item = Item.objects.get(pk=self.kwargs['pk'], owner=self.request.user) #using pk on link. making sure it is owned by user.
        return reverse_lazy('notebook_2:container_detail', kwargs={'pk': item.parentContainer.id}) #an item is deleted from container, so there must be a container.