import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { Expense, Member } from '../core/api.models';
import { GroupsApi } from '../core/groups-api';
import { ExpenseForm } from './expense-form';

describe('ExpenseForm', () => {
  const members: Member[] = [
    { id: 1, name: 'Ana' },
    { id: 2, name: 'Luis' },
    { id: 3, name: 'Marta' },
  ];
  const savedExpense: Expense = {
    id: 10,
    description: 'Cena',
    amountCents: 8450,
    paidBy: 1,
    createdAt: '2026-10-02T10:00:00Z',
    shares: [],
  };

  let fixture: ComponentFixture<ExpenseForm>;
  let element: HTMLElement;
  // Fake API: we only check what the form sends, no HTTP involved.
  const createExpense = vi.fn(() => of(savedExpense));

  beforeEach(async () => {
    createExpense.mockClear();
    await TestBed.configureTestingModule({
      imports: [ExpenseForm],
      providers: [{ provide: GroupsApi, useValue: { createExpense } }],
    }).compileComponents();

    fixture = TestBed.createComponent(ExpenseForm);
    fixture.componentRef.setInput('groupId', 7);
    fixture.componentRef.setInput('members', members);
    fixture.componentRef.setInput('currency', 'EUR');
    element = fixture.nativeElement;
    await fixture.whenStable();
  });

  async function type(selector: string, text: string): Promise<void> {
    const input = element.querySelector<HTMLInputElement>(selector)!;
    input.value = text;
    input.dispatchEvent(new Event('input'));
    await fixture.whenStable();
  }

  function textOf(selector: string): string {
    return (element.querySelector(selector)?.textContent ?? '').replace(/\s+/g, ' ').trim();
  }

  function submitButton(): HTMLButtonElement {
    return element.querySelector<HTMLButtonElement>('button[type=submit]')!;
  }

  it('previews each share of an equal split while typing', async () => {
    await type('#expense-amount', '84,50');

    const shares = [...element.querySelectorAll('.split-list .amount')].map((share) =>
      share.textContent!.replace(/\s+/g, ' ').trim(),
    );
    expect(shares).toEqual(['28,17 €', '28,17 €', '28,16 €']);
  });

  it('sends an equal split with the amount in cents', async () => {
    await type('#expense-description', 'Cena');
    await type('#expense-amount', '84,50');

    submitButton().click();

    expect(createExpense).toHaveBeenCalledWith(7, {
      description: 'Cena',
      amountCents: 8450,
      paidBy: 1,
      split: { mode: 'equal', memberIds: [1, 2, 3] },
    });
  });

  it('only allows saving an exact split when it adds up to the amount', async () => {
    await type('#expense-description', 'Súper');
    await type('#expense-amount', '50');
    element.querySelector<HTMLInputElement>('input[type=radio][value=exact]')!.click();
    await fixture.whenStable();

    await type('#exact-1', '20');
    await type('#exact-2', '25');
    expect(textOf('.exact-status')).toBe('Faltan 5,00 € por repartir.');
    expect(submitButton().disabled).toBe(true);

    await type('#exact-2', '30');
    expect(textOf('.exact-status')).toBe('El reparto cuadra con el importe.');
    expect(submitButton().disabled).toBe(false);

    submitButton().click();
    expect(createExpense).toHaveBeenCalledWith(7, {
      description: 'Súper',
      amountCents: 5000,
      paidBy: 1,
      split: {
        mode: 'exact',
        shares: [
          { memberId: 1, amountCents: 2000 },
          { memberId: 2, amountCents: 3000 },
        ],
      },
    });
  });
});
