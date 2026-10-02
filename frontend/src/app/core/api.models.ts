// Shapes of the JSON sent and received by the backend. All money is in integer cents.

export interface Member {
  id: number;
  name: string;
}

export interface GroupSummary {
  id: number;
  name: string;
  currency: string;
  memberCount: number;
  totalSpentCents: number;
}

export interface Share {
  memberId: number;
  amountCents: number;
}

export interface Expense {
  id: number;
  description: string;
  amountCents: number;
  paidBy: number;
  createdAt: string;
  shares: Share[];
}

export interface Payment {
  id: number;
  fromMemberId: number;
  toMemberId: number;
  amountCents: number;
  createdAt: string;
}

export interface GroupDetail {
  id: number;
  name: string;
  currency: string;
  members: Member[];
  expenses: Expense[];
  payments: Payment[];
}

export interface Balance {
  memberId: number;
  name: string;
  paidCents: number;
  owedCents: number;
  netCents: number;
}

export interface Settlement {
  fromMemberId: number;
  fromName: string;
  toMemberId: number;
  toName: string;
  amountCents: number;
}

export interface NewGroup {
  name: string;
  currency: string;
  members: string[];
}

export interface EqualSplitRequest {
  mode: 'equal';
  memberIds: number[];
}

export interface ExactSplitRequest {
  mode: 'exact';
  shares: Share[];
}

/** The backend picks the split type by looking at "mode". */
export type SplitRequest = EqualSplitRequest | ExactSplitRequest;

export interface NewExpense {
  description: string;
  amountCents: number;
  paidBy: number;
  split: SplitRequest;
}

export interface NewPayment {
  fromMemberId: number;
  toMemberId: number;
  amountCents: number;
}
