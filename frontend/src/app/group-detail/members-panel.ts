import { Component, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Member } from '../core/api.models';
import { apiErrorMessage } from '../core/api-error';
import { GroupsApi } from '../core/groups-api';

@Component({
  selector: 'app-members-panel',
  imports: [FormsModule],
  templateUrl: './members-panel.html',
  styleUrl: './members-panel.css',
})
export class MembersPanel {
  private readonly api = inject(GroupsApi);

  readonly groupId = input.required<number>();
  readonly members = input.required<Member[]>();
  readonly added = output<Member>();

  protected readonly name = signal('');
  protected readonly saving = signal(false);
  protected readonly error = signal<string | null>(null);

  protected submit(): void {
    const name = this.name().trim();
    if (name === '' || this.saving()) {
      return;
    }
    this.saving.set(true);
    this.error.set(null);
    this.api.addMember(this.groupId(), name).subscribe({
      next: (member) => {
        this.saving.set(false);
        this.name.set('');
        this.added.emit(member);
      },
      error: (error) => {
        this.saving.set(false);
        this.error.set(apiErrorMessage(error));
      },
    });
  }
}
