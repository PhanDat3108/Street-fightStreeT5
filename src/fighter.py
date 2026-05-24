import pygame
import random
import math

class Projectile:
    def __init__(self, x, y, direction, damage=10, speed=15, is_skill_3=False, image=None):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.is_skill_3 = is_skill_3
        self.active = True
        self.image = image
        
        if self.image:
            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y
        else:
            self.rect = pygame.Rect(x, y, 30, 15)

    def update(self, target):
        self.rect.x += self.speed * self.direction
        if self.rect.right < 0 or self.rect.left > pygame.display.Info().current_w:
            self.active = False
            return False
            
        if self.active and self.rect.colliderect(target.rect):
            target.health -= self.damage
            target.hit = True
            target.just_hit = True
            target.last_damage_taken = self.damage
            if self.is_skill_3:
                new_x = target.rect.x + 30 * self.direction
                max_w = pygame.display.Info().current_w
                target.rect.x = max(0, min(new_x, max_w - target.rect.width))
            self.active = False
            return True
        return False

    def draw(self, surface):
        if self.image:
            img = self.image
            if self.direction < 0:
                img = pygame.transform.flip(img, True, False)
            surface.blit(img, (self.rect.x, self.rect.y))
        else:
            pygame.draw.circle(surface, (0, 150, 255), self.rect.center, 20)
            pygame.draw.circle(surface, (255, 255, 255), self.rect.center, 10)

class Fighter:
    def __init__(self, player, x, y, flip, data, sprite_sheet, animation_steps, sound, fighter_type="melee", row_map=None, col_map=None, align_bottom=None, skill_image=None, skill3_sound=None):
        self.player = player
        self.size = data[0]
        self.image_scale = data[1]
        self.offset = data[2]
        self.flip = flip
        self.fighter_type = fighter_type
        self.row_map = row_map
        self.align_bottom = align_bottom
        self.skill_image = skill_image
        self.animation_list = self.load_images(sprite_sheet, animation_steps, row_map, col_map)
        self.action = 0  # 0:idle #1:run #2:jump #3:attack1 #4: attack2 #5:hit #6:death
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]
        self.update_time = pygame.time.get_ticks()
        self.rect = pygame.Rect((x, y, 80, 180))
        self.vel_y = 0
        self.running = False
        self.jump = False
        self.attacking = False
        self.attack_type = 0
        self.attack_cooldown = 0
        self.attack_sound = sound
        self.skill3_sound = skill3_sound
        self.hit = False
        self.just_hit = False
        self.last_damage_taken = 0
        self.combo_finished = False
        self.max_health = 250
        self.health = 250
        self.max_mana = 20
        self.mana = 0
        self.alive = True
        self.projectiles = []
        # AI attributes for computer player
        self.ai_enabled = False  # Changed to False for 2-player mode
        self.ai_reaction_time = 0
        self.ai_decision_cooldown = 0
        self.ai_aggression = 0.85  # Increased aggression (0-1 scale, higher = more aggressive)
        self.ai_defense_threshold = 25  # Lower threshold for defensive behavior
        self.ai_reaction_speed = 5  # Faster reaction time (lower = faster)
        self.ai_predictive_aim = True  # Enable predictive aiming

    def load_images(self, sprite_sheet, animation_steps, row_map=None, col_map=None):
        # extract images from spritesheet
        animation_list = []
        # If size is a list [width, height], use it. Otherwise assume square
        if isinstance(self.size, list) and len(self.size) == 2:
            frame_w, frame_h = self.size[0], self.size[1]
        else:
            frame_w = frame_h = self.size

        for idx, animation in enumerate(animation_steps):
            temp_img_list = []
            y = row_map[idx] if row_map else idx
            start_x = col_map[idx] if col_map else 0
            for i in range(animation):
                try:
                    rect = pygame.Rect((start_x + i) * frame_w, y * frame_h, frame_w, frame_h)
                    temp_img = sprite_sheet.subsurface(rect)
                    
                    # Align sprite to the ground if align_bottom is set
                    if self.align_bottom is not None:
                        bbox = temp_img.get_bounding_rect()
                        if bbox.width > 0:
                            y_offset = self.align_bottom - bbox.bottom
                            if y_offset != 0:
                                aligned_img = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                                aligned_img.blit(temp_img, (0, y_offset))
                                temp_img = aligned_img
                                
                    temp_img_list.append(
                        pygame.transform.scale(temp_img, (int(frame_w * self.image_scale), int(frame_h * self.image_scale))))
                except ValueError:
                    # If out of bounds, use a blank surface to prevent crash
                    blank = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                    temp_img_list.append(pygame.transform.scale(blank, (int(frame_w * self.image_scale), int(frame_h * self.image_scale))))
            animation_list.append(temp_img_list)
        return animation_list

    def ai_make_decision(self, target, screen_width, screen_height):
        """Enhanced AI decision making for computer-controlled fighter"""
        if not self.ai_enabled or not self.alive:
            return 0, 0, False, 0  # dx, dy, jump, attack_type
        
        if self.ai_decision_cooldown > 0:
            self.ai_decision_cooldown -= 1

        # Calculate distance to target
        distance = abs(target.rect.centerx - self.rect.centerx)
        vertical_distance = abs(target.rect.centery - self.rect.centery)
        
        is_defensive = self.health < self.ai_defense_threshold
        
        # Movement decisions
        dx = 0
        dy = 0
        should_jump = False
        attack_type = 0
        
        # Enhanced movement logic
        if distance > 150:  # Too far - approach aggressively
            if target.rect.centerx > self.rect.centerx:
                dx = 8  # Move right
            else:
                dx = -8  # Move left
            self.running = True
        elif distance < 60 and is_defensive:  # Too close and defensive - back away
            if target.rect.centerx > self.rect.centerx:
                dx = -10
            else:
                dx = 10
            self.running = True
        elif distance > 80 and distance <= 150: # Adjust to perfect attack range
            if target.rect.centerx > self.rect.centerx:
                dx = 5
            else:
                dx = -5
            self.running = True

        # Jump logic - throttle chance to avoid bunny hopping
        jump_chance = 0.02 if not is_defensive else 0.04
        if random.random() < jump_chance and not self.jump:
            if distance < 200 or target.jump or target.attacking:
                should_jump = True
        
        # Attack logic
        if distance < 180 and self.attack_cooldown == 0 and self.ai_decision_cooldown == 0:
            # Chance to attack
            if random.random() < self.ai_aggression:
                if target.jump:
                    attack_type = 2
                elif distance < 90:
                    # 40% chance to use combo when close and have enough mana!
                    if random.random() < 0.4 and self.mana >= self.max_mana:
                        attack_type = 3
                    else:
                        attack_type = 1
                else:
                    attack_type = 2
                
                self.ai_decision_cooldown = random.randint(30, 60) # Wait 0.5s - 1s between attacks
        
        return dx, dy, should_jump, attack_type

    def move(self, screen_width, screen_height, target, round_over):
        SPEED = 10
        GRAVITY = 2
        dx = 0
        dy = 0
        self.running = False
        if not self.attacking:
            self.attack_type = 0

        # get keypresses for human player
        key = pygame.key.get_pressed()

        # can only perform other actions if not currently attacking and not being hit
        if self.attacking == False and self.hit == False and self.alive == True and round_over == False:
            # check player 1 controls (human player)
            if self.player == 1:
                # movement
                if key[pygame.K_a]:
                    dx = -SPEED
                    self.running = True
                if key[pygame.K_d]:
                    dx = SPEED
                    self.running = True
                # jump
                if key[pygame.K_w] and self.jump == False:
                    self.vel_y = -30
                    self.jump = True
                # attack
                if (key[pygame.K_r] or key[pygame.K_t] or key[pygame.K_y]) and self.attack_cooldown == 0:
                    if key[pygame.K_r]:
                        self.attack_type = 1
                        self.attack(target, 10)
                    elif key[pygame.K_t]:
                        self.attack_type = 2
                        self.attack(target, 10)
                    elif key[pygame.K_y] and self.mana >= self.max_mana:
                        self.attack_type = 3
                        self.mana -= self.max_mana
                        self.attack(target, 15)

            # check player 2 controls
            elif self.player == 2:
                if self.ai_enabled:
                    # Get AI decisions
                    ai_dx, ai_dy, should_jump, attack_type = self.ai_make_decision(target, screen_width, screen_height)
                    
                    # Apply AI movement
                    if ai_dx != 0:
                        dx = ai_dx
                        self.running = True
                    
                    # Apply AI jump
                    if should_jump and self.jump == False:
                        self.vel_y = -30
                        self.jump = True
                    
                    # Apply AI attack
                    if attack_type > 0 and self.attack_cooldown == 0:
                        self.attack_type = attack_type
                        if attack_type == 1:
                            self.attack(target, 10)
                        elif attack_type == 2:
                            self.attack(target, 10)
                        elif attack_type == 3:
                            # Only execute combo if mana is sufficient
                            if self.mana >= self.max_mana:
                                self.mana -= self.max_mana
                                self.attack(target, 15)
                            else:
                                # Fallback if AI somehow chose 3 without mana
                                self.attack_type = 1
                                self.attack(target, 10)
                else:
                    # Player 2 human controls
                    if key[pygame.K_LEFT]:
                        dx = -SPEED
                        self.running = True
                    if key[pygame.K_RIGHT]:
                        dx = SPEED
                        self.running = True
                    # jump
                    if key[pygame.K_UP] and self.jump == False:
                        self.vel_y = -30
                        self.jump = True
                    # attack
                    if (key[pygame.K_b] or key[pygame.K_n] or key[pygame.K_m]) and self.attack_cooldown == 0:
                        if key[pygame.K_b]:
                            self.attack_type = 1
                            self.attack(target, 10)
                        elif key[pygame.K_n]:
                            self.attack_type = 2
                            self.attack(target, 10)
                        elif key[pygame.K_m] and self.mana >= self.max_mana:
                            self.attack_type = 3
                            self.mana -= self.max_mana
                            self.attack(target, 15)

        # apply gravity
        self.vel_y += GRAVITY
        dy += self.vel_y

        # ensure player stays on screen
        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > screen_width:
            dx = screen_width - self.rect.right
        if self.rect.bottom + dy > screen_height - 110:
            self.vel_y = 0
            self.jump = False
            dy = screen_height - 110 - self.rect.bottom

        # ensure players face each other
        if target.rect.centerx > self.rect.centerx:
            self.flip = False
        else:
            self.flip = True

        # apply attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # update player position
        self.rect.x += dx
        self.rect.y += dy

    # handle animation updates
    def update(self, target=None):
        # check what action the player is performing
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.update_action(6)  # 6:death
        elif self.hit:
            self.update_action(5)  # 5:hit
        elif self.attacking:
            if self.attack_type == 1:
                self.update_action(3)  # 3:attack1
            elif self.attack_type == 2:
                self.update_action(4)  # 4:attack2
            elif self.attack_type == 3:
                if len(self.animation_list) > 7:
                    self.update_action(7)  # 7:attack3
                else:
                    if self.action not in [3, 4]:
                        self.update_action(3)  # Start with attack1
        elif self.jump:
            self.update_action(2)  # 2:jump
        elif self.running:
            self.update_action(1)  # 1:run
        else:
            self.update_action(0)  # 0:idle

        # update projectiles
        if target:
            for p in self.projectiles[:]:
                hit = p.update(target)
                if hit and not p.is_skill_3:
                    self.mana += 5
                    if self.mana > self.max_mana:
                        self.mana = self.max_mana
                if not p.active:
                    self.projectiles.remove(p)

        animation_cooldown = 50
        # update image
        self.image = self.animation_list[self.action][self.frame_index]
        # check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
        # check if the animation has finished
        if self.frame_index >= len(self.animation_list[self.action]):
            # if the player is dead then end the animation
            if not self.alive:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0
                # check if an attack was executed
                if self.action == 3:
                    if self.attack_type == 3 and len(self.animation_list) <= 7:
                        self.action = 4
                        self.frame_index = 0
                        self.update_time = pygame.time.get_ticks()
                        self.attack_sound.play()
                    else:
                        if target:
                            range_mult = 2.5 if self.attack_type == 2 else 2
                            attacking_rect = pygame.Rect(self.rect.centerx - (range_mult * self.rect.width * self.flip), self.rect.y,
                                                         range_mult * self.rect.width, self.rect.height)
                            if attacking_rect.colliderect(target.rect):
                                damage = 10 if self.attack_type in [1, 2] else 20
                                target.health -= damage
                                target.hit = True
                                target.just_hit = True
                                target.last_damage_taken = damage
                                
                                if self.attack_type in [1, 2]:
                                    self.mana += 5
                                    if self.mana > self.max_mana:
                                        self.mana = self.max_mana
                                        
                                if self.attack_type == 3:
                                    push_dir = -1 if self.flip else 1
                                    new_x = target.rect.x + 30 * push_dir
                                    max_w = pygame.display.Info().current_w
                                    target.rect.x = max(0, min(new_x, max_w - target.rect.width))
                                    
                        self.attacking = False
                        self.attack_cooldown = 20
                elif self.action == 4:
                    if target:
                        if self.fighter_type == "ranged":
                            direction = -1 if self.flip else 1
                            spawn_x = self.rect.centerx + (50 * direction)
                            spawn_y = self.rect.centery - 20
                            damage = 10 if self.attack_type in [1, 2] else 20
                            p = Projectile(spawn_x, spawn_y, direction, damage=damage, speed=15, is_skill_3=(self.attack_type == 3), image=self.skill_image if self.attack_type == 3 else None)
                            self.projectiles.append(p)
                        else:
                            range_mult = 2.5 if self.attack_type == 2 else 2
                            attacking_rect = pygame.Rect(self.rect.centerx - (range_mult * self.rect.width * self.flip), self.rect.y,
                                                         range_mult * self.rect.width, self.rect.height)
                            if attacking_rect.colliderect(target.rect):
                                damage = 10 if self.attack_type in [1, 2] else 20
                                target.health -= damage
                                target.hit = True
                                target.just_hit = True
                                target.last_damage_taken = damage
                                
                                if self.attack_type in [1, 2]:
                                    self.mana += 5
                                    if self.mana > self.max_mana:
                                        self.mana = self.max_mana
                                        
                                if self.attack_type == 3:
                                    push_dir = -1 if self.flip else 1
                                    new_x = target.rect.x + 30 * push_dir
                                    max_w = pygame.display.Info().current_w
                                    target.rect.x = max(0, min(new_x, max_w - target.rect.width))
                    self.attacking = False
                    self.attack_cooldown = 20
                    if self.attack_type == 3:
                        self.combo_finished = True
                elif self.action == 7:
                    if target:
                        # Melee hit
                        attacking_rect = pygame.Rect(self.rect.centerx - (2 * self.rect.width * self.flip), self.rect.y,
                                                     2 * self.rect.width, self.rect.height)
                        if attacking_rect.colliderect(target.rect):
                            target.health -= 20
                            target.hit = True
                            target.just_hit = True
                            target.last_damage_taken = 20
                            push_dir = -1 if self.flip else 1
                            new_x = target.rect.x + 30 * push_dir
                            max_w = pygame.display.Info().current_w
                            target.rect.x = max(0, min(new_x, max_w - target.rect.width))
                            
                        # Ranged hit
                        if self.fighter_type in ["ranged", "hybrid"]:
                            direction = -1 if self.flip else 1
                            spawn_x = self.rect.centerx + (50 * direction)
                            spawn_y = self.rect.centery - 20
                            p = Projectile(spawn_x, spawn_y, direction, damage=20, speed=15, is_skill_3=True, image=self.skill_image)
                            self.projectiles.append(p)
                    self.attacking = False
                    self.attack_cooldown = 20
                    if self.attack_type == 3:
                        self.combo_finished = True
                # check if damage was taken
                if self.action == 5:
                    self.hit = False
                    # if the player was in the middle of an attack, then the attack is stopped
                    self.attacking = False
                    self.attack_cooldown = 20

    def attack(self, target, damage=10):
        if self.attack_cooldown == 0:
            # execute attack
            self.attacking = True
            if self.attack_type == 3 and self.skill3_sound:
                self.skill3_sound.play()
            else:
                self.attack_sound.play()

    def update_action(self, new_action):
        # check if the new action is different to the previous one
        if new_action != self.action:
            self.action = new_action
            # update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self, surface):
        img = pygame.transform.flip(self.image, self.flip, False).copy()
        
        # Thêm hiệu ứng chớp đỏ khi nhận sát thương
        if self.hit:
            try:
                mask = pygame.mask.from_surface(img)
                mask_surf = mask.to_surface(setcolor=(255, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
                img.blit(mask_surf, (0, 0))
            except Exception:
                pass

        if isinstance(self.size, (list, tuple)):
            base_width = int(self.size[0] * self.image_scale)
        else:
            base_width = int(self.size * self.image_scale)
            
        extra_width = img.get_width() - base_width
        draw_x = self.rect.x - (self.offset[0] * self.image_scale)
        if self.flip and extra_width > 0:
            draw_x -= extra_width
            
        surface.blit(img, (draw_x, self.rect.y - (self.offset[1] * self.image_scale)))
        
        for p in self.projectiles:
            p.draw(surface)
