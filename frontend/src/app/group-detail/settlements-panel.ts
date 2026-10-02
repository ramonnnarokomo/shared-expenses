import { Component, input, output } from '@angular/core';

import { Settlement } from '../core/api.models';
import { MoneyPipe } from '../core/money.pipe';

@Component({
  selector: 'app-settlements-panel',
  imports: [MoneyPipe],
  templateUrl: './settlements-panel.html',
  styleUrl: './settlements-panel.css',
})
export class SettlementsPanel {
  readonly settlements = input.required<Settlement[]>();
  readonly currency = input.required<string>();
  /** True while a payment is being saved, to avoid double clicks. */
  readonly busy = input(false);
  readonly markAsPaid = output<Settlement>();
}
