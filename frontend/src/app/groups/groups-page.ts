import { Component, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { GroupDetail, GroupSummary } from '../core/api.models';
import { apiErrorMessage } from '../core/api-error';
import { GroupsApi } from '../core/groups-api';
import { MoneyPipe } from '../core/money.pipe';
import { NewGroupForm } from './new-group-form';

@Component({
  selector: 'app-groups-page',
  imports: [RouterLink, MoneyPipe, NewGroupForm],
  templateUrl: './groups-page.html',
  styleUrl: './groups-page.css',
})
export class GroupsPage implements OnInit {
  private readonly api = inject(GroupsApi);
  private readonly router = inject(Router);

  protected readonly groups = signal<GroupSummary[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listGroups().subscribe({
      next: (groups) => {
        this.groups.set(groups);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(apiErrorMessage(error));
        this.loading.set(false);
      },
    });
  }

  protected openGroup(group: GroupDetail): void {
    this.router.navigate(['/groups', group.id]);
  }
}
