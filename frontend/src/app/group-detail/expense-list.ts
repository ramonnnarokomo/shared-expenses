import { DatePipe } from '@angular/common';
import { Component, input, output } from '@angular/core';

import { Expense } from '../core/api.models';
import { formatMoney } from '../core/money';
import { MoneyPipe } from '../core/money.pipe';

@Component({
  selector: 'app-expense-list',
  imports: [DatePipe, MoneyPipe],
  templateUrl: './expense-list.html',
  styleUrl: './expense-list.css',
})
export class ExpenseList {
  readonly expenses = input.required<Expense[]>();
  readonly memberNames = input.required<Map<number, string>>();
  readonly currency = input.required<string>();
  /** The page asks for confirmation and deletes it. */
  readonly remove = output<Expense>();

  protected nameOf(memberId: number): string {
    return this.memberNames().get(memberId) ?? '¿?';
  }

  /** "Ana 28,17 € · Luis 28,17 € · Marta 28,16 €" */
  protected shareSummary(expense: Expense): string {
    return expense.shares
      .map((share) => {
        const amount = formatMoney(share.amountCents, this.currency());
        return `${this.nameOf(share.memberId)} ${amount}`;
      })
      .join(' · ');
  }
}
