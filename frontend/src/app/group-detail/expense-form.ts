import { Component, computed, inject, input, linkedSignal, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Expense, Member, NewExpense, Share, SplitRequest } from '../core/api.models';
import { apiErrorMessage } from '../core/api-error';
import { GroupsApi } from '../core/groups-api';
import { parseEurosToCents } from '../core/money';
import { MoneyPipe } from '../core/money.pipe';
import { splitEqually } from '../core/split';

type SplitMode = 'equal' | 'exact';

@Component({
  selector: 'app-expense-form',
  imports: [FormsModule, MoneyPipe],
  templateUrl: './expense-form.html',
  styleUrl: './expense-form.css',
})
export class ExpenseForm {
  private readonly api = inject(GroupsApi);

  readonly groupId = input.required<number>();
  readonly members = input.required<Member[]>();
  readonly currency = input.required<string>();
  readonly created = output<Expense>();

  // ----- Form state (bound to the inputs with [(ngModel)]) -----
  protected readonly description = signal('');
  protected readonly amountText = signal('');
  protected readonly mode = signal<SplitMode>('equal');
  /** Exact mode: the text typed for each member id. */
  protected readonly exactTexts = signal<Partial<Record<number, string>>>({});
  protected readonly saving = signal(false);
  protected readonly error = signal<string | null>(null);

  // linkedSignal: a writable signal that goes back to its default whenever the members change.
  /** Who paid. Defaults to the first member. */
  protected readonly paidBy = linkedSignal<number | null>(() => this.members()[0]?.id ?? null);
  /** Equal mode: who takes part, in the order of the member list. Defaults to everyone. */
  protected readonly selectedIds = linkedSignal(() => this.members().map((member) => member.id));

  // ----- Values derived from the form -----
  protected readonly amountCents = computed(() => parseEurosToCents(this.amountText()));
  protected readonly amountInvalid = computed(
    () => this.amountText().trim() !== '' && (this.amountCents() ?? 0) <= 0,
  );

  /** Live preview of each share in equal mode. */
  protected readonly equalShares = computed(() =>
    splitEqually(this.amountCents() ?? 0, this.selectedIds()),
  );

  /** Exact mode: cents per member. An empty box counts as 0; an invalid one as null. */
  protected readonly exactShares = computed(() =>
    this.members().map((member) => {
      const text = (this.exactTexts()[member.id] ?? '').trim();
      return { memberId: member.id, amountCents: text === '' ? 0 : parseEurosToCents(text) };
    }),
  );
  protected readonly exactHasInvalid = computed(() =>
    this.exactShares().some((share) => share.amountCents === null),
  );
  protected readonly exactAssignedCents = computed(() =>
    this.exactShares().reduce((total, share) => total + (share.amountCents ?? 0), 0),
  );
  /** Positive: money still to assign ("faltan"). Negative: assigned too much ("sobran"). */
  protected readonly exactRemaining = computed(
    () => (this.amountCents() ?? 0) - this.exactAssignedCents(),
  );

  protected readonly canSubmit = computed(() => {
    const amount = this.amountCents();
    const basicsOk =
      this.description().trim() !== '' && amount !== null && amount > 0 && this.paidBy() !== null;
    const splitOk =
      this.mode() === 'equal'
        ? this.selectedIds().length > 0
        : !this.exactHasInvalid() && this.exactRemaining() === 0;
    return basicsOk && splitOk && !this.saving();
  });

  protected isSelected(memberId: number): boolean {
    return this.selectedIds().includes(memberId);
  }

  protected toggleMember(memberId: number, checked: boolean): void {
    const selected = new Set(this.selectedIds());
    if (checked) {
      selected.add(memberId);
    } else {
      selected.delete(memberId);
    }
    // Keep the order of the member list: it decides who gets the extra cents.
    this.selectedIds.set(
      this.members()
        .map((member) => member.id)
        .filter((id) => selected.has(id)),
    );
  }

  protected setExactText(memberId: number, text: string): void {
    this.exactTexts.update((texts) => ({ ...texts, [memberId]: text }));
  }

  protected submit(): void {
    const amountCents = this.amountCents();
    const paidBy = this.paidBy();
    if (!this.canSubmit() || amountCents === null || paidBy === null) {
      return;
    }
    this.saving.set(true);
    this.error.set(null);

    const expense: NewExpense = {
      description: this.description().trim(),
      amountCents,
      paidBy,
      split: this.buildSplit(),
    };
    this.api.createExpense(this.groupId(), expense).subscribe({
      next: (created) => {
        this.saving.set(false);
        this.reset();
        this.created.emit(created);
      },
      error: (error) => {
        this.saving.set(false);
        this.error.set(apiErrorMessage(error));
      },
    });
  }

  private buildSplit(): SplitRequest {
    if (this.mode() === 'equal') {
      return { mode: 'equal', memberIds: this.selectedIds() };
    }
    // Members left at 0 are not part of the expense, so we do not send them.
    const shares = this.exactShares().filter(
      (share): share is Share => (share.amountCents ?? 0) > 0,
    );
    return { mode: 'exact', shares };
  }

  private reset(): void {
    this.description.set('');
    this.amountText.set('');
    this.exactTexts.set({});
    this.selectedIds.set(this.members().map((member) => member.id));
  }
}
