import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { App } from './app';
import { ToastService } from './core/toast.service';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('shows the app name in the header', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();

    const brand = (fixture.nativeElement as HTMLElement).querySelector('.brand');
    expect(brand?.textContent).toContain('Gastos compartidos');
  });

  it('renders the toasts of the ToastService', async () => {
    const fixture = TestBed.createComponent(App);
    TestBed.inject(ToastService).success('Gasto añadido');
    await fixture.whenStable();

    const toast = (fixture.nativeElement as HTMLElement).querySelector('.toast');
    expect(toast?.textContent).toContain('Gasto añadido');
  });
});
