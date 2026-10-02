import { Component, computed, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { GroupDetail } from '../core/api.models';
import { apiErrorMessage } from '../core/api-error';
import { GroupsApi } from '../core/groups-api';
import { ToastService } from '../core/toast.service';

@Component({
  selector: 'app-new-group-form',
  imports: [FormsModule],
  templateUrl: './new-group-form.html',
  styleUrl: './new-group-form.css',
})
export class NewGroupForm {
  private readonly api = inject(GroupsApi);
  private readonly toasts = inject(ToastService);

  readonly created = output<GroupDetail>();

  protected readonly currencies = ['EUR', 'USD', 'GBP'];
  protected readonly name = signal('');
  protected readonly currency = signal('EUR');
  protected readonly memberDraft = signal('');
  protected readonly members = signal<string[]>([]);
  protected readonly saving = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly canSubmit = computed(
    () => this.name().trim() !== '' && this.members().length >= 2 && !this.saving(),
  );

  protected addMember(): void {
    const name = this.memberDraft().trim();
    if (name === '') {
      return;
    }
    const alreadyAdded = this.members().some(
      (member) => member.toLowerCase() === name.toLowerCase(),
    );
    if (alreadyAdded) {
      this.error.set(`${name} ya está en la lista`);
      return;
    }
    this.members.update((members) => [...members, name]);
    this.memberDraft.set('');
    this.error.set(null);
  }

  protected removeMember(name: string): void {
    this.members.update((members) => members.filter((member) => member !== name));
  }

  protected submit(): void {
    if (!this.canSubmit()) {
      return;
    }
    this.saving.set(true);
    this.error.set(null);
    this.api
      .createGroup({ name: this.name().trim(), currency: this.currency(), members: this.members() })
      .subscribe({
        next: (group) => {
          this.saving.set(false);
          this.toasts.success(`Grupo «${group.name}» creado`);
          this.created.emit(group);
        },
        error: (error) => {
          this.saving.set(false);
          this.error.set(apiErrorMessage(error));
        },
      });
  }
}
