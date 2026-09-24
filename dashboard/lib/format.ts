/** Display IDs: patients as PID-0001, doctors as DID-0001. */

export const pid = (id: number) => `PID-${String(id).padStart(4, "0")}`;
export const did = (id: number) => `DID-${String(id).padStart(4, "0")}`;

export const bmi = (weightKg: number, heightCm: number) => {
  const heightM = heightCm / 100;
  return weightKg / (heightM * heightM);
};
