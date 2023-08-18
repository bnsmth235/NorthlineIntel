from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from ..models import Project, Group, Subgroup, STATE_OPTIONS, STATUS_OPTIONS

@login_required(login_url='projectmanagement:login')
def home(request):
    recent_projects = Project.objects.order_by('-date', '-status')[:5]
    context = {'recent_projects': recent_projects}
    return render(request, 'projects/home.html', context)


@login_required(login_url='projectmanagement:login')
def all(request):
    projects = Project.objects.order_by('-date', '-status')
    context = {'projects': projects}
    return render(request, 'projects/all_proj.html', context)


@login_required(login_url='projectmanagement:login')
def project_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    return render(request, 'projects/project_view.html', {'project': project})


@login_required(login_url='projectmanagement:login')
def new_proj(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip = request.POST.get('zip')
        date = datetime.now()
        edited_by = request.user.username
        status = "I"

        if not name or not address or not city or not state or not zip:
            return render(request, 'projects/new_proj.html', {'error_message': "Please fill out all fields",
                                                             'state_options': STATE_OPTIONS})

        if int(zip) < 10000 and zip != "":
            return render(request, 'projects/new_proj.html', {'error_message': "Zip code incorrect",
                                                             'state_options': STATE_OPTIONS})

        project = Project(name=name, date=date, edited_by=edited_by, status=status,
                           address=address, city=city, state=state, zip=zip)
        project.save()
        print("Project " + project.name + " has been saved")

        group_index = 0

        for key in request.POST:
            if key.startswith('group_'):
                print("********************")
                print("Found key")
                print("********************")
                group_name = request.POST[key]
                print("********************")
                print("Group Name: " + group_name)
                print("********************")
                subgroup_key = f'subgroup_{group_index}'
                subgroup_names = request.POST.getlist(subgroup_key)

                if group_name:
                    group = Group(name=group_name, project_id=project)
                    group.save()

                    for subgroup_name in subgroup_names:
                        print("********************")
                        print("Found Subgroup: " + subgroup_name)
                        print("********************")
                        if subgroup_name:
                            subgroup = Subgroup(name=subgroup_name, group_id=group)
                            subgroup.save()

                group_index += 1

        return redirect('projectmanagement:home')

    return render(request, 'projects/new_proj.html', {"state_options": STATE_OPTIONS})


@login_required(login_url='projectmanagement:login')
def edit_proj(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip = request.POST.get('zip')
        status = request.POST.get('status')
        print("***********************")
        print(status)
        print("***********************")
        date = datetime.now()
        edited_by = request.user.username

        if not name or not address or not city or not state or not zip:
            return render(request, 'projects/edit_project.html', {'error_message': "Please fill out all fields",
                                                                  'project': project,
                                                                  'state_options': STATE_OPTIONS,
                                                                  'status_options': STATUS_OPTIONS})

        if (int(zip) < 0 or int(zip) > 99999) and zip != "":
            return render(request, 'projects/edit_project.html', {'error_message': "Zip code incorrect",
                                                                  'project': project,
                                                                  'state_options': STATE_OPTIONS,
                                                                  'status_options': STATUS_OPTIONS})

        project.name = name
        project.address = address
        project.city = city
        project.state = state
        project.zip = zip
        project.status = status
        project.date = date
        project.edited_by = edited_by
        project.save()

        return redirect('projectmanagement:home')

    return render(request, 'projects/edit_project.html', {'project': project,
                                                          'state_options': STATE_OPTIONS,'status_options': STATUS_OPTIONS})


@login_required(login_url='projectmanagement:login')
def delete_proj(request, project_id):
    if request.method == 'POST':
        username = request.POST.get('username')
        print("Attempting to delete")

        if username == request.user.username:
            project = get_object_or_404(Project, pk=project_id)
            project.delete()
            print("Project deleted")
        else:
            print("Username incorrect")

    return redirect('projectmanagement:home')
