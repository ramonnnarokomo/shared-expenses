import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, input, numberAttribute, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { Balance, Expense, GroupDetail, Member, Settlement } from '../core/api.models';
import { apiErrorMessage } from '../core/api-error';
import { GroupsApi } from '../core/groups-api';
import { MoneyPipe } from '../core/money.pipe';
import { ToastService } from '../core/toast.service';
import { BalancesPanel } from './balances-panel';
import { ExpenseForm } from './expense-form';
import { ExpenseList } from './expense-list';
import { MembersPanel } from './members-panel';
import { SettlementsPanel } from './settlements-panel';

/**
 * Owns the data of one group. Child components display it, and after any change
 * the page reloads group, balances and settlements so everything stays consistent.
 */
@Component({
  selector: 'app-group-detail-page',
  imports: [
    RouterLink,
    DatePipe,
    MoneyPipe,
    BalancesPanel,
    ExpenseForm,
    ExpenseList,
    MembersPanel,
    SettlementsPanel,
  ],
  templateUrl: './group-detail-page.html',
  styleUrl: './group-detail-page.css',
})
export class GroupDetailPage implements OnInit {
  private readonly api = inject(GroupsApi);
  private readonly toasts = inject(ToastService);

  /** The :id of the route (see withComponentInputBinding in app.config.ts). */
  readonly id = input.required({ transform: numberAttribute });

  protected readonly group = signal<GroupDetail | null>(null);
  protected readonly balances = signal<Balance[]>([]);
  protected readonly settlements = signal<Settlement[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly savingPayment = signal(false);

  protected readonly totalSpentCents = computed(
    () => this.group()?.expenses.reduce((total, expense) => total + expense.amountCents, 0) ?? 0,
  );

  protected readonly memberNames = computed(
    () => new Map(this.group()?.members.map((member) => [member.id, member.name]) ?? []),
  );

  ngOnInit(): void {
    this.load();
  }

  protected load(): void {
    // "Cargando…" only while there is nothing to show; later reloads keep the current data on screen.
    this.loading.set(this.group() === null);
    this.error.set(null);
    forkJoin({
      group: this.api.getGroup(this.id()),
      balances: this.api.getBalances(this.id()),
      settlements: this.api.getSettlements(this.id()),
    }).subscribe({
      next: ({ group, balances, settlements }) => {
        this.group.set(group);
        this.balances.set(balances);
        this.settlements.set(settlements);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(apiErrorMessage(error));
        this.loading.set(false);
      },
    });
  }

  protected deleteExpense(expense: Expense): void {
    if (!window.confirm(`¿Seguro que quieres borrar el gasto «${expense.description}»?`)) {
      return;
    }
    this.api.deleteExpense(this.id(), expense.id).subscribe({
      next: () => {
        this.toasts.success('Gasto borrado');
        this.load();
      },
      error: (error) => this.toasts.error(apiErrorMessage(error)),
    });
  }

  protected markAsPaid(settlement: Settlement): void {
    this.savingPayment.set(true);
    const payment = {
      fromMemberId: settlement.fromMemberId,
      toMemberId: settlement.toMemberId,
      amountCents: settlement.amountCents,
    };
    this.api.createPayment(this.id(), payment).subscribe({
      next: () => {
        this.savingPayment.set(false);
        this.toasts.success(`Pago de ${settlement.fromName} a ${settlement.toName} registrado`);
        this.load();
      },
      error: (error) => {
        this.savingPayment.set(false);
        this.toasts.error(apiErrorMessage(error));
      },
    });
  }

  protected onExpenseCreated(): void {
    this.toasts.success('Gasto añadido');
    this.load();
  }

  protected onMemberAdded(member: Member): void {
    this.toasts.success(`${member.name} se ha unido al grupo`);
    this.load();
  }
}
