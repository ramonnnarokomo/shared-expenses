import { Component, computed, input } from '@angular/core';

import { Balance } from '../core/api.models';
import { MoneyPipe } from '../core/money.pipe';

@Component({
  selector: 'app-balances-panel',
  imports: [MoneyPipe],
  templateUrl: './balances-panel.html',
  styleUrl: './balances-panel.css',
})
export class BalancesPanel {
  readonly balances = input.required<Balance[]>();
  readonly currency = input.required<string>();

  /** Each balance plus the length of its bar, relative to the largest balance (0-100). */
  protected readonly rows = computed(() => {
    const largest = Math.max(1, ...this.balances().map((balance) => Math.abs(balance.netCents)));
    return this.balances().map((balance) => ({
      ...balance,
      barPercent: (Math.abs(balance.netCents) / largest) * 100,
    }));
  });
}
