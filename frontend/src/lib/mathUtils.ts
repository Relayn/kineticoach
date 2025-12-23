export interface Landmark {
  x: number;
  y: number;
  z: number;
  visibility: number;
}

export function calculateAngle(p1: Landmark, p2: Landmark, p3: Landmark): number {
  const v1 = { x: p1.x - p2.x, y: p1.y - p2.y };
  const v2 = { x: p3.x - p2.x, y: p3.y - p2.y };

  const dot = v1.x * v2.x + v1.y * v2.y;
  const norm = Math.sqrt(v1.x ** 2 + v1.y ** 2) * Math.sqrt(v2.x ** 2 + v2.y ** 2);

  if (norm === 0) return 0;

  const cosine = Math.max(-1, Math.min(1, dot / norm));
  return Math.acos(cosine) * (180 / Math.PI);
}

/**
 * Вычисляет угол позвоночника для упражнения Cat-Cow.
 * Использует landmarks: nose (0), shoulders (11,12), hips (23,24).
 *
 * @param landmarks Массив из 33 landmarks от MediaPipe.
 * @returns Угол позвоночника в градусах (140-200).
 */
export function calculateSpineAngle(landmarks: Landmark[]): number {
  if (landmarks.length < 25) return 0;

  const nose = landmarks[0];
  const leftShoulder = landmarks[11];
  const rightShoulder = landmarks[12];
  const leftHip = landmarks[23];
  const rightHip = landmarks[24];

  // Середина плеч
  const midShoulder: Landmark = {
    x: (leftShoulder.x + rightShoulder.x) / 2,
    y: (leftShoulder.y + rightShoulder.y) / 2,
    z: (leftShoulder.z + rightShoulder.z) / 2,
    visibility: Math.min(leftShoulder.visibility, rightShoulder.visibility),
  };

  // Середина бедер
  const midHip: Landmark = {
    x: (leftHip.x + rightHip.x) / 2,
    y: (leftHip.y + rightHip.y) / 2,
    z: (leftHip.z + rightHip.z) / 2,
    visibility: Math.min(leftHip.visibility, rightHip.visibility),
  };

  // Угол: нос - середина плеч - середина бедер
  return calculateAngle(nose, midShoulder, midHip);
}

/**
 * Вычисляет относительную высоту головы для упражнения Cat-Cow.
 *
 * @param landmarks Массив из 33 landmarks от MediaPipe.
 * @returns Разница по Y между носом и плечами (отрицательная = голова выше плеч).
 */
export function calculateHeadHeight(landmarks: Landmark[]): number {
  if (landmarks.length < 13) return 0;

  const nose = landmarks[0];
  const leftShoulder = landmarks[11];
  const rightShoulder = landmarks[12];

  const midShoulderY = (leftShoulder.y + rightShoulder.y) / 2;

  // Отрицательное значение = голова выше плеч (поза "корова")
  // Положительное значение = голова ниже плеч (поза "кошка")
  return nose.y - midShoulderY;
}
