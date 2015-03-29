import random

def calc_piece_rotations(v1, v2, v3):
	if v1 == v2 == v3:
		return ((v1, v2, v3),)
	else:
		return ((v1, v2, v3), (v2, v3, v1), (v3, v1, v2))


pieces = tuple(enumerate((
		calc_piece_rotations(0, 0, 0),
		calc_piece_rotations(0, 0, 1),
		calc_piece_rotations(0, 0, 2),
		calc_piece_rotations(0, 0, 3),
		calc_piece_rotations(0, 1, 1),
		calc_piece_rotations(0, 1, 2),
		calc_piece_rotations(0, 1, 2),
		calc_piece_rotations(0, 1, 2),
		calc_piece_rotations(0, 2, 1),
		calc_piece_rotations(0, 2, 1),
		calc_piece_rotations(0, 2, 1),
		calc_piece_rotations(0, 2, 2),
		calc_piece_rotations(0, 3, 3),
		calc_piece_rotations(1, 1, 1),
		calc_piece_rotations(1, 2, 3),
		calc_piece_rotations(1, 2, 3),
		calc_piece_rotations(2, 1, 3),
		calc_piece_rotations(2, 1, 3),
		calc_piece_rotations(2, 2, 2),
		calc_piece_rotations(3, 3, 3)
	)))

faces = (
		(0, 1, 2),
		(0, 2, 3),
		(0, 3, 4),
		(0, 4, 5),
		(0, 5, 1),
		(1, 5, 6),
		(1, 6, 7),
		(1, 7, 2),
		(2, 7, 8),
		(2, 8, 3),
		(3, 8, 9),
		(3, 9, 4),
		(4, 10, 5),
		(4, 9, 10),
		(5, 10, 6),
		(6, 10, 11),
		(6, 11, 7),
		(7, 11, 8),
		(8, 11, 9),
		(11, 10, 9)
	)


class Solver:
	NUM_FACE_PIECES = 20         # how many faces/pieces there are (len(faces))
	NUM_PEGS = 12                # how many pegs/vertices there are (len(pieces))
	NUM_FACES_AROUND_VERTEX = 5  # how many faces share a single vertex
	MAX_CORNER_VALUE = 3         # largest possible value found on corner/vertex of any piece

	def __init__(self):
		self._reset()

	def _reset(self):
		self._piece_availability = [True] * Solver.NUM_FACE_PIECES
		self._vert_sums = [0] * Solver.NUM_PEGS
		self._num_pieces_around_verts = [0] * Solver.NUM_PEGS
		self._placements = [None] * Solver.NUM_FACE_PIECES
		self._num_steps = 0
		self._pegs = None

	def _is_placement_valid(self, rotated_piece, face_index):
		v1, v2, v3 = faces[face_index]
		
		num_spaces_around_v1 = Solver.NUM_FACES_AROUND_VERTEX - (self._num_pieces_around_verts[v1]+1)
		num_spaces_around_v2 = Solver.NUM_FACES_AROUND_VERTEX - (self._num_pieces_around_verts[v2]+1)
		num_spaces_around_v3 = Solver.NUM_FACES_AROUND_VERTEX - (self._num_pieces_around_verts[v3]+1)

		v1_sum_remaining = self._pegs[v1] - (self._vert_sums[v1] + rotated_piece[0])
		v2_sum_remaining = self._pegs[v2] - (self._vert_sums[v2] + rotated_piece[1])
		v3_sum_remaining = self._pegs[v3] - (self._vert_sums[v3] + rotated_piece[2])

		# no vertex may be over-capacity and no vertex may have so much spare capacity that it is impossible to complete
		return (v1_sum_remaining >= 0 and v1_sum_remaining <= num_spaces_around_v1*Solver.MAX_CORNER_VALUE and
		        v2_sum_remaining >= 0 and v2_sum_remaining <= num_spaces_around_v2*Solver.MAX_CORNER_VALUE and
		        v3_sum_remaining >= 0 and v3_sum_remaining <= num_spaces_around_v3*Solver.MAX_CORNER_VALUE)

	def _place_piece(self, piece_index, rotated_piece, face_index):
		self._placements[face_index] = rotated_piece
		self._piece_availability[piece_index] = False

		v1, v2, v3 = faces[face_index]
		self._vert_sums[v1] += rotated_piece[0]
		self._vert_sums[v2] += rotated_piece[1]
		self._vert_sums[v3] += rotated_piece[2]

		self._num_pieces_around_verts[v1] += 1
		self._num_pieces_around_verts[v2] += 1
		self._num_pieces_around_verts[v3] += 1

	def _unplace_piece(self, piece_index, rotated_piece, face_index):
		self._placements[face_index] = None
		self._piece_availability[piece_index] = True

		v1, v2, v3 = faces[face_index]
		self._vert_sums[v1] -= rotated_piece[0]
		self._vert_sums[v2] -= rotated_piece[1]
		self._vert_sums[v3] -= rotated_piece[2]

		self._num_pieces_around_verts[v1] -= 1
		self._num_pieces_around_verts[v2] -= 1
		self._num_pieces_around_verts[v3] -= 1

	def _select_face_to_solve(self):
		best_face_index = None
		min_score = 999999
		face_index = -1
		for face_index, (v1, v2, v3) in enumerate(faces):
			if self._placements[face_index] != None: continue

			v1_sum_remaining = self._pegs[v1] - self._vert_sums[v1]
			v2_sum_remaining = self._pegs[v2] - self._vert_sums[v2]
			v3_sum_remaining = self._pegs[v3] - self._vert_sums[v3]
			num_spaces_around_v1 = Solver.NUM_FACES_AROUND_VERTEX - self._num_pieces_around_verts[v1]
			num_spaces_around_v2 = Solver.NUM_FACES_AROUND_VERTEX - self._num_pieces_around_verts[v2]
			num_spaces_around_v3 = Solver.NUM_FACES_AROUND_VERTEX - self._num_pieces_around_verts[v3]

			# score based on spare vertex capacity and surrounding face availability
			# these quantities are weighted against their maximum possible value which seems to produce better results
			score = (
				(v1_sum_remaining + v2_sum_remaining + v3_sum_remaining) / NUM_PEGS +
				(num_spaces_around_v1 + num_spaces_around_v2 + num_spaces_around_v3) / NUM_FACES_AROUND_VERTEX)

			if score < min_score:
				min_score = score
				best_face_index = face_index
				
		return best_face_index


	def _solve_recursively(self, num_placed):
		self._num_steps += 1
		prev_piece = None
		face_index = self._select_face_to_solve()

		for piece_index, piece_rotations in pieces:

			# skip this piece if it is already used
			if not self._piece_availability[piece_index]: continue

			# skip this piece if it is identical to the last
			if piece_rotations[0] == prev_piece: continue
			prev_piece = piece_rotations[0]
			
			for rotated_piece in piece_rotations:
				if self._is_placement_valid(rotated_piece, face_index):
					self._place_piece(piece_index, rotated_piece, face_index)
					# success if we placed the last piece or had success further down the line
					if (num_placed == Solver.NUM_FACE_PIECES or
						self._solve_recursively(num_placed+1)):
						return True
					self._unplace_piece(piece_index, rotated_piece, face_index)

		return False

	def solve(self, pegs):
		self._reset()
		self._pegs = pegs
		return self._placements, self._num_steps if self._solve_recursively(1) else None

if __name__ == "__main__":

	# generate a random peg arrangement to solve
	pegs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
	random.shuffle(pegs)

	print("Solving peg arrangement: " + str(pegs))

	placements, num_steps = Solver().solve(pegs)

	if not placements:
		print("No Solution Available!")
	else:
		print("Solution found in " + str(num_steps) + " steps:")
		for face, piece in zip(faces, placements):
		    peg1 = pegs[face[0]]
		    peg2 = pegs[face[1]]
		    peg3 = pegs[face[2]]
		    print("Piece {0} on Face <{1}, {2}, {3}>".format(piece, peg1, peg2, peg3))