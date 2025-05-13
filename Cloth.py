import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import time
import cv2

class Cloth(nn.Module):
    def __init__(self, height, width, spacing, mass, gravity, stiffness=4.,alpha=0.003, decay=0.99997, init_energy=1e3, device="cuda", method="verlet"):
        super(Cloth, self).__init__() 
        self.width = width
        self.height = height
        self.spacing = spacing
        x = np.arange(0, width * spacing, spacing)
        y = np.arange(0, height * spacing, spacing)
        self.pos = torch.tensor(np.array(np.meshgrid(y, x)).T.reshape(-1, 2), dtype=torch.float32).view(height, width, 2)
        self.prev_pos = self.pos.clone()
        self.velo = torch.zeros_like(self.pos)
        self.mass = mass
        self.gravity = gravity
        self.stiffness = stiffness
        # self.dir = [(0, 1),(1, 0), (1, 1), (-1, 1), (0, -1), (-1, 0), (-1, -1), (1, -1)]
        self.dir = [(0, 1),(1, 0), (0, -1), (-1, 0)]
        self.last_t = None
        self.method = method  
        self.couu = 0
        self.device = device
        # Move tensors to GPU once during initialization
        self.pos = self.pos.to(self.device)
        self.prev_pos = self.prev_pos.to(self.device)
        self.velo = self.velo.to(self.device)
        self.energy_l = torch.tensor(init_energy, device=self.device, dtype=torch.float32)

        self.alpha = alpha
        self.decay = decay

    def forward(self):
        with torch.no_grad(): 
            """Update cloth physics and return frame"""
            if self.last_t is None:
                del_t = 1 / 150
                self.last_t = time.time()
            else:
                tt = time.time()
                del_t = tt - self.last_t
                self.last_t = tt
            del_t *= 150
            force = torch.zeros_like(self.pos, device=self.pos.device)
            force[:, :, 0] = -self.gravity * self.mass
            for ii, jj in self.dir:
                diff = self.pos[max(0, -ii):self.height - max(0, ii), max(0, -jj):self.width - max(0, jj)] - self.pos[max(0, ii):self.height - max(0, -ii), max(0, jj):self.width - max(0, -jj)]
                # f = -diff * torch.norm(diff, dim=2, keepdim=True)
                f = -diff*self.stiffness
                force[max(0, -ii):self.height - max(0, ii), max(0, -jj):self.width - max(0, jj)] += f
            
            idxx1 = torch.arange(0, self.pos.shape[1]//2, 9, device=self.pos.device)
            idxx2 = torch.arange(0, self.pos.shape[1], 9, device=self.pos.device)
            force[-1, idxx1] = 0
            force[0, idxx2] = 0

            if self.method == "verlet":
                newpos = 2 * self.pos - self.prev_pos + force / self.mass * (del_t ** 2)
            elif self.method == "euler":
                newpos = self.pos + self.velo * del_t
                self.velo = self.velo + force / self.mass * del_t

            vel = torch.norm(newpos - self.pos, dim=2, keepdim=True)

            # vel = torch.clamp(vel, 0, self.spacing * 0.5)
            # vel = 2/(2+torch.exp(-5*vel)) - 2/3

            energy = (vel**2).sum()
            print("Energy: ", energy.item(), self.energy_l.item(), self.pos.device)
            energy_n = min(energy, self.energy_l) * self.decay

            pp = 0.8 if self.method == "verlet" else 1
            energy_n = energy_n * pp + energy * (1 - pp)

            vel *= energy_n / (energy + 1e-6)
            self.energy_l = self.energy_l * (1-self.alpha) + (energy_n) * self.alpha

            vel_dir = torch.nn.functional.normalize(newpos - self.pos, dim=2)
            newpos = self.pos + vel_dir * vel
            if self.method == "verlet":
                self.prev_pos = self.pos.clone()
            self.pos = newpos
            # print(self.pos.device)

            # Convert positions directly to image array
            img_size = (804, 804, 3)  # Define your desired output size
            frame = np.zeros(img_size, dtype=np.uint8)
            frame_t = torch.zeros(img_size, dtype=torch.uint8).to(self.device)

            # Scale positions to image coordinates
            
            x = self.pos[:, :, 1].clone()
            y = self.pos[:, :, 0].clone()
            x = ((x / self.width) * (img_size[1] - 20) + 10)
            y = ((y / self.height) * (img_size[0] - 700) + 690)

            x = torch.clamp(x, 0, img_size[1] - 1).long()
            y = torch.clamp(y, 0, img_size[0] - 1).long()

            frame_t[y, x] = torch.tensor([0, 255, 0], dtype=torch.uint8, device=self.device)

            frame_t = frame_t[2:802, 2:802] 

            # x = x.cpu().numpy().astype(np.int32)
            # y = y.cpu().numpy().astype(np.int32)

            # # Draw points
            # for i in range(x.shape[0]):
            #     for j in range(x.shape[1]):
            #         cv2.circle(frame, (x[i, j], y[i, j]), 2, (0, 0, 255), -1)

            # cv2.circle(frame, (10, 10), 5, (0, 255, 0), -1) 

            # Draw lines between points
            # for i in range(x.shape[0]):
            #     for j in range(x.shape[1] - 1):
            #         cv2.line(frame, (x[i, j], y[i, j]), (x[i, j + 1], y[i, j + 1]), (128, 128, 128), 1)
            # for i in range(x.shape[0] - 1):
            #     for j in range(x.shape[1]):
            #         cv2.line(frame, (x[i, j], y[i, j]), (x[i + 1, j], y[i + 1, j]), (128, 128, 128), 1)

            return frame_t.cpu().numpy()